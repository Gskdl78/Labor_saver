#!/usr/bin/env python3
"""修復版後端服務 - 優化版本"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import json
import os
import logging
import asyncio
import traceback
import ollama
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# ==================== 配置管理類 ====================
class Config:
    """集中式配置管理"""
    # 基礎路徑
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / '勞保資料集'
    
    # 資料檔案路徑
    QA_DATABASE = BASE_DIR / '常見問題資料庫.json'
    DISABILITY_STANDARDS_TABLE = DATA_DIR / '勞工保險失能給付標準第三條附表.json'
    OCCUPATIONAL_RULES = DATA_DIR / '勞工職業災害保險職業傷病審查準則.json'
    MEDICAL_BENEFITS = DATA_DIR / '勞工職業災害保險醫療給付介紹.json'
    BENEFIT_STANDARDS = DATA_DIR / '各失能等級之給付標準.json'
    LABOR_OFFICES = DATA_DIR / '勞保局各地辦事處.json'
    HOSPITALS = DATA_DIR / '衛生福利部評鑑合格之醫院名單.json'
    HOSPITALS_WITH_COORDS = DATA_DIR / '衛生福利部評鑑合格之醫院名單_含經緯度.json'
    
    # API 設定
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # Ollama 設定
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma3:4b')
    
    # ChromaDB 設定
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')
    CHROMA_COLLECTION_NAME = "labor_insurance_knowledge"
    
    # 嵌入模型設定
    EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
    
    # 快取設定
    CACHE_MAX_SIZE = 1000
    
    # 查詢設定
    VECTOR_SEARCH_TOP_K = 5  # 增加檢索數量，確保涵蓋更多候選答案
    SIMILARITY_THRESHOLD = 0.6  # 相似度閾值
    
    # 執行緒池設定
    THREAD_POOL_MAX_WORKERS = 4  # 執行緒池最大工作執行緒數
    
    # 速率限制設定
    RATE_LIMIT_REQUESTS = 20  # 每個時間窗口的最大請求數
    RATE_LIMIT_WINDOW = 60  # 時間窗口（秒）
    
    @classmethod
    def validate(cls):
        """驗證配置"""
        if not cls.DATA_DIR.exists():
            logger.warning(f"資料目錄不存在: {cls.DATA_DIR}")
        if not 1024 <= cls.API_PORT <= 65535:
            raise ValueError(f"API 端口必須在 1024-65535 之間，當前: {cls.API_PORT}")
        return True

# ==================== 自訂異常類 ====================
class OllamaConnectionError(Exception):
    """Ollama 連接錯誤"""
    pass

class VectorDatabaseError(Exception):
    """向量資料庫錯誤"""
    pass

class DataLoadError(Exception):
    """資料載入錯誤"""
    pass

# ==================== 日誌設定 ====================
from logging.handlers import RotatingFileHandler

# 確保日誌目錄存在
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# 設置日誌處理器
handlers = [
    # 主控台處理器
    logging.StreamHandler(),
    # 檔案處理器（自動輪替，最大10MB，保留5個備份）
    RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)
logger.info(f"日誌系統已初始化，日誌目錄: {log_dir}")

# 驗證配置
try:
    Config.validate()
    logger.info("配置驗證通過")
except Exception as e:
    logger.error(f"配置驗證失敗: {e}")
    raise

# ==================== 執行緒池（用於非同步處理阻塞操作） ====================
executor = ThreadPoolExecutor(max_workers=Config.THREAD_POOL_MAX_WORKERS)
logger.info(f"執行緒池已建立：{Config.THREAD_POOL_MAX_WORKERS} 個工作執行緒")

# 創建 FastAPI 應用
app = FastAPI(
    title="勞資屬道山",
    description="提供勞災保險諮詢、地圖搜索和失能給付查詢服務",
    version="2.0.0"
)

# 應用生命週期事件
@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理資源"""
    logger.info("正在關閉執行緒池...")
    executor.shutdown(wait=True)
    logger.info("執行緒池已關閉")

# ==================== 速率限制中間件 ====================
class RateLimitMiddleware(BaseHTTPMiddleware):
    """簡單的速率限制中間件（基於 IP）"""
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)
        self.cleanup_interval = 60  # 清理間隔（秒）
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        # 獲取客戶端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 定期清理過期記錄
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_records(current_time)
            self.last_cleanup = current_time
        
        # 檢查速率限制（僅對 API 端點）
        if request.url.path.startswith("/api/"):
            # 移除超出時間窗口的記錄
            self.request_counts[client_ip] = [
                ts for ts in self.request_counts[client_ip]
                if current_time - ts < Config.RATE_LIMIT_WINDOW
            ]
            
            # 檢查請求數是否超過限制
            if len(self.request_counts[client_ip]) >= Config.RATE_LIMIT_REQUESTS:
                logger.warning(f"速率限制觸發: IP {client_ip} 超過 {Config.RATE_LIMIT_REQUESTS} 次/分鐘")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "請求過於頻繁，請稍後再試",
                        "detail": f"每 {Config.RATE_LIMIT_WINDOW} 秒最多 {Config.RATE_LIMIT_REQUESTS} 次請求"
                    }
                )
            
            # 記錄此次請求
            self.request_counts[client_ip].append(current_time)
        
        # 繼續處理請求
        response = await call_next(request)
        return response
    
    def _cleanup_old_records(self, current_time):
        """清理過期的請求記錄"""
        to_delete = []
        for ip, timestamps in self.request_counts.items():
            # 移除超出時間窗口的記錄
            self.request_counts[ip] = [
                ts for ts in timestamps
                if current_time - ts < Config.RATE_LIMIT_WINDOW
            ]
            # 如果該 IP 沒有任何記錄，標記刪除
            if not self.request_counts[ip]:
                to_delete.append(ip)
        
        for ip in to_delete:
            del self.request_counts[ip]

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:61269", "http://127.0.0.1:3000", "http://127.0.0.1:61269"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加速率限制中間件
app.add_middleware(RateLimitMiddleware)
logger.info(f"速率限制已啟用：{Config.RATE_LIMIT_REQUESTS} 次/{Config.RATE_LIMIT_WINDOW} 秒")

# 預設問題和固定答案
PRESET_QA = {
    "什麼是勞工保險": "勞工保險是政府設立的社會保險制度，保障勞工在生病、傷病、生育、職災等情況下的醫療、撫卹等保障。",
    "勞工保險失能給付": "失能給付分15級，按平均日投保薪資×日數計算。第1級1200日，第15級30日。",
    "如何申請失能給付": "1.準備失能診斷書 2.填寫申請書 3.向勞保局申請 4.等待審核結果。",
    "失能等級如何判定": "由健保特約醫院或診所出具失能診斷書，依勞工保險失能給付標準判定等級。",
    "失能給付金額": "普通傷病：第1級1200日，第15級30日。職業傷病：第1級1800日，第15級45日。",
    "申請失能給付需要什麼文件": "失能診斷書、申請書、身分證明、投保資料等相關文件。",
    "失能給付多久可以領到": "申請後約1-2個月內審核完成，通過後即可領取給付。",
    "失能給付可以領幾次": "失能給付為一次給付，領取後即結案。",
    "什麼是職業傷病": "因執行職務而致傷害或疾病，包括職業災害和職業病。",
    "職業傷病給付標準": "職業傷病失能給付比普通傷病高1.5倍，如第1級1800日。",
    "失能診斷書哪裡開": "健保特約醫院或診所，部分項目需醫學中心或區域醫院以上。",
    "失能給付申請資格": "勞保被保險人，經治療後症狀固定，再行治療仍不能期待其治療效果者。",
    "失能給付計算方式": "平均日投保薪資 × 失能等級對應日數 = 給付金額。",
    "失能給付免稅嗎": "失能給付免納所得稅，但需依規定申報。",
    "失能給付可以分期領取嗎": "失能給付為一次給付，無法分期領取。",
    "失能等級如何評估": "失能等級評估依據失能程度、康復可能性、以及對生活功能造成的影響。由健保特約醫院出具失能診斷書，依勞工保險失能給付標準判定等級，分為15級，第1級最嚴重（1200日），第15級最輕微（30日）。評估時會考慮身體機能、工作能力、日常生活自理能力等因素。"
}

# ==================== 快取機制 ====================
@lru_cache(maxsize=Config.CACHE_MAX_SIZE)
def get_cached_embedding(question: str) -> tuple:
    """快取問題的嵌入向量"""
    if not embedding_model:
        return ()
    try:
        embedding = embedding_model.encode([question]).tolist()[0]
        return tuple(embedding)
    except Exception as e:
        logger.error(f"生成嵌入向量失敗: {e}")
        return ()

# ==================== 資料載入函數 ====================
def load_json_file(file_path: Path, description: str = "資料") -> Optional[Any]:
    """通用 JSON 檔案載入函數，含錯誤處理"""
    try:
        if not file_path.exists():
            logger.warning(f"{description}檔案不存在: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"成功載入{description}: {file_path.name}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"{description} JSON 解析錯誤: {e}")
        raise DataLoadError(f"{description}格式錯誤")
    except Exception as e:
        logger.error(f"載入{description}失敗: {e}")
        return None

def load_qa_database():
    """載入常見問題資料庫"""
    return load_json_file(Config.QA_DATABASE, "常見問題資料庫")

# 載入常見問題資料庫
qa_database = load_qa_database()

# 初始化 ChromaDB 和 Sentence Transformer
try:
    # 初始化 ChromaDB
    chroma_client = chromadb.Client(Settings(
        persist_directory=Config.CHROMA_DB_PATH,
        anonymized_telemetry=False
    ))
    
    # 初始化 Sentence Transformer (使用中文模型)
    embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)
    
    # 創建或獲取集合（使用 cosine 距離度量）
    collection = chroma_client.get_or_create_collection(
        name=Config.CHROMA_COLLECTION_NAME,
        metadata={
            "description": "勞工保險知識庫",
            "hnsw:space": "cosine"  # 使用余弦距離
        }
    )
    
    logger.info("ChromaDB 和 Sentence Transformer 初始化成功")
    logger.info(f"向量資料庫路徑: {Config.CHROMA_DB_PATH}")
except Exception as e:
    logger.error(f"初始化 ChromaDB 失敗: {e}")
    raise VectorDatabaseError(f"向量資料庫初始化失敗: {e}")

# 載入所有勞保資料集到向量數據庫
def load_all_datasets_to_vector_db():
    """載入所有勞保資料集到向量數據庫"""
    if not collection or not embedding_model:
        logger.warning("ChromaDB 或 embedding_model 未初始化，跳過向量數據庫載入")
        return False
    
    try:
        # 檢查是否已經有數據
        existing_count = collection.count()
        if existing_count > 0:
            logger.info(f"向量數據庫已有 {existing_count} 條記錄，跳過重新載入")
            return True
        
        documents = []
        metadatas = []
        ids = []
        
        # 1. 載入失能給付標準第三條附表
        try:
            disability_standards = load_json_file(
                Config.DISABILITY_STANDARDS_TABLE, 
                "失能給付標準第三條附表"
            )
            if not disability_standards:
                raise DataLoadError("失能給付標準載入失敗")
            
            for item in disability_standards:
                doc_text = f"""
失能種類：{item.get('失能種類', '')}
失能項目：{item.get('失能項目', '')}
失能狀態：{item.get('失能狀態', '')}
失能等級：{item.get('失能等級', '')}
失能審核基準：{item.get('失能審核基準', '')}
開具診斷書醫療機構層級：{item.get('開具診斷書醫療機構層級', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "勞工保險失能給付標準第三條附表",
                    "type": "失能給付標準",
                    "失能等級": item.get('失能等級', ''),
                    "失能種類": item.get('失能種類', '')
                })
                ids.append(f"disability_{item.get('編號', uuid.uuid4())}")
                
        except Exception as e:
            logger.error(f"載入失能給付標準失敗: {e}")
        
        # 2. 載入職業傷病審查準則
        try:
            occupational_rules = load_json_file(
                Config.OCCUPATIONAL_RULES,
                "職業傷病審查準則"
            )
            if not occupational_rules:
                raise DataLoadError("職業傷病審查準則載入失敗")
            
            for item in occupational_rules:
                doc_text = f"""
條號：{item.get('條號', '')}
內容：{item.get('內容', '')}
修正發布日期：{item.get('修正發布日期（民國年月日）', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "勞工職業災害保險職業傷病審查準則",
                    "type": "職業傷病審查",
                    "條號": item.get('條號', '')
                })
                ids.append(f"occupational_{item.get('序號', uuid.uuid4())}")
                
        except Exception as e:
            logger.error(f"載入職業傷病審查準則失敗: {e}")
        
        # 3. 載入醫療給付介紹
        try:
            medical_benefits = load_json_file(
                Config.MEDICAL_BENEFITS,
                "醫療給付介紹"
            )
            if not medical_benefits:
                raise DataLoadError("醫療給付介紹載入失敗")
            
            for item in medical_benefits:
                doc_text = f"""
項目：{item.get('項目', '')}
說明：{item.get('說明', '')}
法規：{item.get('法規', '')}
適用起日：{item.get('適用起日（民國年月日）', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "勞工職業災害保險醫療給付介紹",
                    "type": "醫療給付",
                    "項目": item.get('項目', '')
                })
                ids.append(f"medical_{uuid.uuid4()}")
                
        except Exception as e:
            logger.error(f"載入醫療給付介紹失敗: {e}")
        
        # 4. 載入各失能等級之給付標準
        try:
            benefit_standards = load_json_file(
                Config.BENEFIT_STANDARDS,
                "各失能等級給付標準"
            )
            if not benefit_standards:
                raise DataLoadError("給付標準載入失敗")
            
            for item in benefit_standards:
                doc_text = f"""
失能等級：{item.get('失能等級', '')}
普通傷病失能補助費給付標準：{item.get('普通傷病失能補助費給付標準', '')}
職業傷病失能補償費給付標準：{item.get('職業傷病失能補償費給付標準', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "各失能等級之給付標準",
                    "type": "給付標準",
                    "失能等級": item.get('失能等級', '')
                })
                ids.append(f"benefit_{item.get('失能等級', uuid.uuid4())}")
                
        except Exception as e:
            logger.error(f"載入給付標準失敗: {e}")
        
        # 5. 載入勞保局辦事處資料
        try:
            labor_offices = load_json_file(
                Config.LABOR_OFFICES,
                "勞保局辦事處"
            )
            if not labor_offices:
                raise DataLoadError("勞保局辦事處資料載入失敗")
            
            for item in labor_offices:
                doc_text = f"""
縣市別：{item.get('縣市別', '')}
辦事處地址：{item.get('辦事處地址', '')}
辦事處電話：{item.get('辦事處電話', '')}
櫃台服務時間：{item.get('櫃台服務時間', '')}
電話服務時間：{item.get('電話服務時間', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "勞保局各地辦事處",
                    "type": "辦事處資訊",
                    "縣市別": item.get('縣市別', '')
                })
                ids.append(f"office_{uuid.uuid4()}")
                
        except Exception as e:
            logger.error(f"載入勞保局辦事處失敗: {e}")
        
        # 6. 載入醫院名單
        try:
            hospitals = load_json_file(
                Config.HOSPITALS,
                "醫院名單"
            )
            if not hospitals:
                raise DataLoadError("醫院名單載入失敗")
            
            for item in hospitals:
                doc_text = f"""
醫院名稱：{item.get('醫院名稱', '')}
所在縣市：{item.get('所在縣市', '')}
醫院評鑑評鑑結果：{item.get('醫院評鑑評鑑結果', '')}
醫院電話：{item.get('醫院電話', '')}
地址：{item.get('地址', '')}
                """.strip()
                
                documents.append(doc_text)
                metadatas.append({
                    "source": "衛生福利部評鑑合格之醫院名單",
                    "type": "醫院資訊",
                    "所在縣市": item.get('所在縣市', ''),
                    "醫院名稱": item.get('醫院名稱', '')
                })
                ids.append(f"hospital_{uuid.uuid4()}")
                
        except Exception as e:
            logger.error(f"載入醫院名單失敗: {e}")
        
        # 批次添加到向量數據庫（優化：分批處理）
        if documents:
            batch_size = 100  # 每批處理 100 條記錄
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            logger.info(f"開始批次載入 {len(documents)} 條記錄，分 {total_batches} 批處理")
            
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                batch_docs = documents[i:batch_end]
                batch_metas = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]
                
                # 生成嵌入向量（批次）
                batch_embeddings = embedding_model.encode(batch_docs).tolist()
                
                # 添加到 ChromaDB
                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids,
                    embeddings=batch_embeddings
                )
                
                batch_num = (i // batch_size) + 1
                logger.info(f"批次 {batch_num}/{total_batches} 完成（{batch_end}/{len(documents)} 條記錄）")
            
            logger.info(f"✅ 成功載入 {len(documents)} 條記錄到向量數據庫")
            return True
        else:
            logger.warning("沒有找到任何文檔來載入")
            return False
            
    except Exception as e:
        logger.error(f"載入向量數據庫失敗: {e}")
        return False

# 初始化時載入所有資料集
load_all_datasets_to_vector_db()

# 初始化 Ollama 客戶端
try:
    ollama_client = ollama.Client(host=Config.OLLAMA_HOST)
    logger.info(f"Ollama 客戶端初始化成功: {Config.OLLAMA_HOST}")
except Exception as e:
    logger.error(f"Ollama 客戶端初始化失敗: {e}")
    ollama_client = None

# ==================== Pydantic 模型（輸入驗證） ====================

class ChatRequest(BaseModel):
    """聊天請求模型"""
    message: str = Field(..., min_length=1, max_length=500, description="用戶問題")
    session_id: str = Field(default="default", max_length=100, description="會話ID")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('問題不能為空')
        return v.strip()

class ChatResponse(BaseModel):
    """聊天回應模型"""
    response: str
    sources: List[str]
    success: bool

class BodyPartInjuryRequest(BaseModel):
    """身體部位傷害分析請求"""
    body_part: str = Field(..., min_length=2, max_length=50, description="身體部位")
    injury_description: str = Field(..., min_length=5, max_length=500, description="傷害描述")
    
    @field_validator('body_part')
    @classmethod
    def validate_body_part(cls, v):
        allowed_parts = [
            '頭部', '頸部', '上肢', '下肢', '軀幹', '胸腹部', 
            '眼', '耳', '鼻', '口', '手', '腳', '背部', '腰部',
            '精神', '神經', '皮膚', '頭', '臉', '手指', '腳趾'
        ]
        if not any(part in v for part in allowed_parts):
            logger.warning(f"未識別的身體部位: {v}")
        return v.strip()

class DisabilityBenefitRequest(BaseModel):
    """失能給付查詢請求"""
    level: int = Field(..., ge=1, le=15, description="失能等級 (1-15)")
    injury_type: str = Field(default="普通傷病", description="傷病類型")
    
    @field_validator('injury_type')
    @classmethod
    def validate_injury_type(cls, v):
        allowed_types = ["普通傷病", "職業傷病", "職業災害", "職業", "普通"]
        if v not in allowed_types:
            return "普通傷病"
        return v

class NearbyLocationRequest(BaseModel):
    """附近位置查詢請求"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    type: str = Field(default="hospital", description="位置類型")
    radius: float = Field(default=50, ge=1, le=200, description="搜索半徑（公里）")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ["hospital", "labor_office"]
        if v not in allowed_types:
            raise ValueError(f'類型必須是 {allowed_types} 之一')
        return v

# ==================== 非同步包裝函數 ====================
async def async_ollama_generate(client, model: str, prompt: str, options: dict) -> dict:
    """非同步包裝 Ollama 生成函數（在執行緒池中運行）"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: client.generate(model=model, prompt=prompt, options=options)
    )

async def async_vector_search(question: str, top_k: int = None) -> List[dict]:
    """非同步包裝向量搜索（在執行緒池中運行）"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: search_vector_database(question, top_k)
    )

# ==================== 原有函數 ====================
def find_preset_answer(question: str) -> str:
    """查找預設問題的答案 - 優先使用JSON資料庫"""
    question = question.strip()
    
    # 1. 優先使用JSON資料庫
    if qa_database:
        answer = search_qa_database(question)
        if answer:
            return answer
    
    # 2. 回退到原始PRESET_QA
    if question in PRESET_QA:
        return PRESET_QA[question]
    
    # 3. 關鍵字匹配
    for preset_q, answer in PRESET_QA.items():
        clean_question = question.replace("？", "").replace("?", "").replace("。", "")
        clean_preset = preset_q.replace("？", "").replace("?", "").replace("。", "")
        
        if any(keyword in clean_question for keyword in clean_preset.split()):
            return answer
    
    return ""

def search_vector_database(question: str, top_k: int = None) -> List[dict]:
    """在向量數據庫中搜索相關文檔（使用快取）"""
    if not collection or not embedding_model:
        logger.warning("向量資料庫或嵌入模型未初始化")
        return []
    
    if top_k is None:
        top_k = Config.VECTOR_SEARCH_TOP_K
    
    try:
        # 使用快取獲取查詢向量
        query_embedding = get_cached_embedding(question)
        if not query_embedding:
            logger.error("無法生成查詢向量")
            return []
        
        # 搜索相似文檔（取更多候選，便於過濾）
        results = collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=top_k * 2,  # 多取一些候選
            include=['documents', 'metadatas', 'distances']
        )
        
        # 格式化結果並過濾低相似度結果
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else 1.0
                similarity = 1 - distance  # 轉換距離為相似度
                
                # 只保留高相似度結果
                if similarity >= Config.SIMILARITY_THRESHOLD:
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': distance,
                        'similarity': round(similarity, 3)
                    })
        
        # 返回 top_k 個結果
        return formatted_results[:top_k]
        
    except chromadb.errors.ChromaError as e:
        logger.error(f"ChromaDB 錯誤: {e}")
        raise VectorDatabaseError(f"向量資料庫查詢失敗: {e}")
    except Exception as e:
        logger.error(f"向量數據庫搜索失敗: {traceback.format_exc()}")
        return []

def search_qa_database(question: str) -> str:
    """在JSON資料庫中搜索答案"""
    if not qa_database:
        return ""
    
    clean_question = question.replace("？", "").replace("?", "").replace("。", "")
    
    # 1. 直接匹配
    for category, questions in qa_database["常見問題"].items():
        for q, answer in questions.items():
            if q == question or q == clean_question:
                return answer
    
    # 2. 關鍵詞匹配
    for category, questions in qa_database["常見問題"].items():
        for q, answer in questions.items():
            clean_q = q.replace("？", "").replace("?", "").replace("。", "")
            if any(keyword in clean_question for keyword in clean_q.split()):
                return answer
    
    # 3. 使用快速查詢關鍵詞
    if "快速查詢關鍵詞" in qa_database:
        for keyword, synonyms in qa_database["快速查詢關鍵詞"].items():
            if any(syn in clean_question for syn in synonyms):
                # 找到相關關鍵詞，搜索對應答案
                for category, questions in qa_database["常見問題"].items():
                    for q, answer in questions.items():
                        if keyword in q or any(syn in q for syn in synonyms):
                            return answer
    
    return ""

@app.get("/")
async def root():
    return {"message": "勞資屬道山 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/chat/preset-questions")
async def get_preset_questions():
    """獲取預設問題列表"""
    questions = []
    
    # 優先從JSON資料庫獲取
    if qa_database and "常見問題" in qa_database:
        for category, qa_dict in qa_database["常見問題"].items():
            questions.extend(list(qa_dict.keys()))
    else:
        # 回退到原始PRESET_QA
        questions = list(PRESET_QA.keys())
    
    return {
        "questions": questions,
        "total": len(questions)
    }

@app.get("/api/rag/status")
async def get_rag_status():
    """獲取RAG系統狀態"""
    try:
        if not collection:
            return {
                "status": "error",
                "message": "ChromaDB 未初始化",
                "vector_db_count": 0
            }
        
        count = collection.count()
        return {
            "status": "healthy",
            "message": "RAG系統運行正常",
            "vector_db_count": count,
            "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
            "collections": ["labor_insurance_knowledge"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RAG系統狀態檢查失敗: {str(e)}",
            "vector_db_count": 0
        }

@app.post("/api/rag/reload")
async def reload_vector_database():
    """重新載入向量數據庫"""
    try:
        if not collection:
            return {
                "success": False,
                "message": "ChromaDB 未初始化"
            }
        
        # 清空現有數據
        collection.delete()
        
        # 重新載入
        success = load_all_datasets_to_vector_db()
        
        if success:
            count = collection.count()
            return {
                "success": True,
                "message": f"成功重新載入 {count} 條記錄",
                "record_count": count
            }
        else:
            return {
                "success": False,
                "message": "重新載入失敗"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"重新載入失敗: {str(e)}"
        }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG增強版聊天 API（含完善錯誤處理 + 非同步處理）"""
    try:
        # 0. 【優先】檢查是否為常見問題，直接從資料庫快速回答
        faq_answer = search_qa_database(request.message)
        if faq_answer and faq_answer.strip():
            logger.info(f"✅ 常見問題快速回答: {request.message[:50]}")
            return ChatResponse(
                response=faq_answer,
                sources=["常見問題資料庫"],
                success=True
            )
        
        # 1. 如果不是常見問題，使用RAG系統搜索相關文檔（非同步）
        try:
            relevant_docs = await async_vector_search(request.message)
            logger.info(f"找到 {len(relevant_docs)} 個相關文檔")
        except VectorDatabaseError as e:
            logger.warning(f"向量資料庫查詢失敗，使用降級策略: {e}")
            relevant_docs = []
        
        # 2. 如果向量搜索沒有結果，嘗試使用預設答案（備用）
        if not relevant_docs:
            preset_answer = find_preset_answer(request.message)
            if preset_answer and preset_answer.strip():
                logger.info(f"向量搜索無結果，使用預設答案回覆問題: {request.message[:50]}")
                return ChatResponse(
                    response=preset_answer,
                    sources=["預設知識庫"],
                    success=True
                )
        
        # 3. 智能排序和構建基於文檔的提示詞
        context_text = ""
        sources = []
        
        if relevant_docs:
            # 智能排序：優先顯示與問題關鍵詞完全匹配的文檔
            def calc_keyword_match_score(doc, question):
                """計算關鍵詞匹配分數"""
                doc_text = doc['document'].lower()
                question_lower = question.lower()
                score = 0
                
                # 提取問題中的關鍵短語
                key_phrases = []
                if "僅能從事輕便工作" in question:
                    key_phrases.append("僅能從事輕便工作")
                if "終身無工作能力" in question:
                    key_phrases.append("終身無工作能力")
                if "終身僅能從事輕便工作" in question:
                    key_phrases.append("終身僅能從事輕便工作")
                
                # 計算匹配分數
                for phrase in key_phrases:
                    if phrase.lower() in doc_text:
                        score += 10  # 關鍵短語完全匹配，高權重
                
                return score
            
            # 為每個文檔計算綜合分數（相似度 + 關鍵詞匹配）
            scored_docs = []
            for doc in relevant_docs:
                similarity = doc.get('similarity', 0)
                keyword_score = calc_keyword_match_score(doc, request.message)
                total_score = similarity + (keyword_score * 0.05)  # 關鍵詞匹配增加額外分數
                scored_docs.append((total_score, doc))
            
            # 按綜合分數降序排序
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            
            # 構建 context（優先顯示高分結果）
            for total_score, doc in scored_docs:
                similarity = doc.get('similarity', 0)
                context_text += f"\n相關資訊（相似度: {similarity:.3f}）：\n{doc['document']}\n"
                source_name = doc['metadata'].get('source', '未知來源')
                if source_name not in sources:
                    sources.append(source_name)
        
        # 4. 使用 Ollama 生成回答（非同步）
        if not ollama_client:
            raise OllamaConnectionError("Ollama 客戶端未初始化")
        
        prompt = f"""你是勞資屬道山諮詢助手，專門回答勞工保險相關問題。請根據以下相關資料回答問題。

問題：{request.message}

相關資料：
{context_text}

重要提示：
1. 請**仔細閱讀**用戶問題中的每一個關鍵詞，特別注意「終身無工作能力」vs「終身僅能從事輕便工作」等細微差別
2. 請從相關資料中找出**完全匹配**用戶描述狀況的條目
3. 不同的失能狀態對應不同的失能等級，請確保選擇正確的等級
4. 如果資料中有失能等級資訊，請明確指出等級數字

請根據以上資料用繁體中文回答，提供準確、專業的資訊。回答請控制在200字以內："""

        try:
            response = await async_ollama_generate(
                ollama_client,
                Config.OLLAMA_MODEL,
                prompt,
                {
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'max_tokens': 300,
                }
            )
            answer = response['response'].strip()
        except Exception as e:
            logger.error(f"Ollama 生成回答失敗: {e}")
            raise OllamaConnectionError(f"AI 模型回應失敗: {e}")
        
        # 5. 處理回答
        if not relevant_docs:
            answer += "\n\n注意：此問題的相關資料可能不在我們的知識庫中，建議您直接聯繫勞保局或相關機構獲得更準確的資訊。"
            sources = ["AI 語言模型"]
        else:
            sources.append("AI 語言模型")
        
        logger.info(f"成功回覆問題，使用資料來源: {sources}")
        return ChatResponse(
            response=answer,
            sources=sources,
            success=True
        )
    
    # 分類錯誤處理
    except OllamaConnectionError as e:
        logger.error(f"Ollama 連接錯誤: {e}")
        # 降級策略：返回提示訊息
        return ChatResponse(
            response="AI 服務暫時無法使用，請稍後再試或直接聯繫勞保局：0800-078-777",
            sources=["系統訊息"],
            success=False
        )
    except VectorDatabaseError as e:
        logger.error(f"向量資料庫錯誤: {e}")
        return ChatResponse(
            response="知識庫查詢暫時無法使用，請稍後再試。您也可以直接撥打勞保局專線：0800-078-777",
            sources=["系統訊息"],
            success=False
        )
    except ValueError as e:
        logger.error(f"輸入驗證錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"未預期的錯誤: {traceback.format_exc()}")
        return ChatResponse(
            response="抱歉，處理您的問題時發生錯誤，請稍後再試。",
            sources=[],
            success=False
        )

@app.post("/api/disability/body-part")
async def analyze_body_part_injury(request: BodyPartInjuryRequest):
    """根據身體部位和傷害描述分析可能的失能等級（含輸入驗證）"""
    try:
        if not ollama_client:
            raise OllamaConnectionError("Ollama 客戶端未初始化")
        
        # 構建分析提示詞
        prompt = f"""你是勞工保險失能給付標準專家。請根據以下資訊分析可能的失能等級：

身體部位：{request.body_part}
傷害描述：{request.injury_description}

勞工保險失能給付標準分為12類：精神、神經、眼、耳、鼻、口、胸腹部臟器、軀幹、頭臉頸、皮膚、上肢、下肢。

失能等級1-15級對應給付日數：
- 1級：普通1200日，職業1800日
- 2級：普通1000日，職業1500日  
- 3級：普通840日，職業1260日
- 4級：普通740日，職業1110日
- 5級：普通640日，職業960日
- 6級：普通540日，職業810日
- 7級：普通440日，職業660日
- 8級：普通360日，職業540日
- 9級：普通280日，職業420日
- 10級：普通220日，職業330日
- 11級：普通160日，職業240日
- 12級：普通100日，職業150日
- 13級：普通60日，職業90日
- 14級：普通40日，職業60日
- 15級：普通30日，職業45日

請根據傷害嚴重程度分析可能的失能等級，並提供簡潔說明。

回答格式：
- 可能失能等級：X級
- 說明：[簡潔說明原因]
- 給付日數：普通傷病X日，職業傷病X日

請用繁體中文回答，限制在100字以內："""

        # 使用 Ollama 生成分析（非同步）
        response = await async_ollama_generate(
            ollama_client,
            Config.OLLAMA_MODEL,
            prompt,
            {
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 150,
            }
        )
        
        analysis = response['response'].strip()
        logger.info(f"成功分析身體部位傷害: {request.body_part}")
        
        return {
            "body_part": request.body_part,
            "injury_description": request.injury_description,
            "analysis": analysis,
            "success": True
        }
    
    except OllamaConnectionError as e:
        logger.error(f"Ollama 連接錯誤: {e}")
        return {
            "error": "AI 服務暫時無法使用，請稍後再試",
            "success": False
        }
    except ValueError as e:
        logger.error(f"輸入驗證錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"身體部位分析失敗: {traceback.format_exc()}")
        return {
            "error": "分析身體部位傷害時發生錯誤",
            "success": False
        }

# 載入失能給付標準數據
def load_disability_benefit_standards():
    """載入失能給付標準數據"""
    return load_json_file(Config.BENEFIT_STANDARDS, "失能給付標準")

# 載入失能給付標準
disability_standards = load_disability_benefit_standards()

@app.post("/api/disability/benefit")
async def get_disability_benefit(request: DisabilityBenefitRequest):
    """根據失能等級查詢給付標準（含輸入驗證）"""
    try:
        logger.info(f"查詢失能給付: level={request.level}, injury_type={request.injury_type}")
        
        if not disability_standards:
            return {"error": "失能給付標準數據載入失敗", "success": False}
        
        # 從JSON數據中查找對應等級
        level_data = None
        for standard in disability_standards:
            if standard["失能等級"] == str(request.level):
                level_data = standard
                break
        
        if not level_data:
            raise ValueError(f"無效的失能等級: {request.level}")
        
        # 提取給付日數
        ordinary_days = int(level_data["普通傷病失能補助費給付標準"].replace("日", ""))
        occupational_days = int(level_data["職業傷病失能補償費給付標準"].replace("日", ""))
        
        # 確定傷病類型
        if request.injury_type in ["職業傷病", "職業災害", "職業"]:
            benefit_type = "職業"
            benefit_days = occupational_days
        else:
            benefit_type = "普通"
            benefit_days = ordinary_days
        
        # 構建詳細說明
        severity = '較嚴重' if request.level <= 5 else '中等' if request.level <= 10 else '較輕微'
        
        explanation = f"""失能等級第{request.level}級給付標準：

給付日數：{benefit_days}日
傷病類型：{request.injury_type}
給付標準：{benefit_type}傷病

說明：
• 失能等級第{request.level}級屬於{severity}的失能程度
• 給付日數依勞工保險失能給付標準計算
• 職業傷病給付日數為普通傷病的1.5倍
• 實際給付金額需依投保薪資計算

注意事項：
• 需由健保特約醫院出具失能診斷書
• 申請時需檢附相關醫療證明文件
• 給付標準可能因法規修訂而調整"""
        
        logger.info(f"成功查詢失能給付: 等級{request.level}，類型{request.injury_type}")
        return {
            "level": request.level,
            "injury_type": request.injury_type,
            "benefit_type": benefit_type,
            "benefit_days": benefit_days,
            "ordinary_days": ordinary_days,
            "occupational_days": occupational_days,
            "general_benefit": f"{ordinary_days}日",
            "occupational_benefit": f"{occupational_days}日",
            "explanation": explanation,
            "success": True
        }
    
    except ValueError as e:
        logger.error(f"輸入驗證錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"查詢失能給付失敗: {traceback.format_exc()}")
        return {
            "error": "查詢失能給付時發生錯誤",
            "success": False
        }

# 載入地圖數據
def load_map_data():
    """載入地圖相關數據"""
    try:
        # 載入勞保局辦事處數據
        labor_offices = load_json_file(Config.LABOR_OFFICES, "勞保局辦事處")
        
        # 載入醫院數據（使用含經緯度的版本）
        hospitals = load_json_file(Config.HOSPITALS_WITH_COORDS, "醫院名單（含經緯度）")
        
        if not labor_offices or not hospitals:
            raise DataLoadError("地圖數據載入不完整")
        
        logger.info(f"成功載入地圖數據：辦事處 {len(labor_offices)} 個，醫院 {len(hospitals)} 家")
        return {
            "labor_offices": labor_offices,
            "hospitals": hospitals
        }
    except Exception as e:
        logger.error(f"載入地圖數據失敗: {e}")
        return None

# 載入地圖數據
map_data = load_map_data()

@app.get("/api/maps/cities")
async def get_cities():
    """獲取所有城市列表"""
    if not map_data:
        return {"error": "地圖數據載入失敗", "success": False}
    
    cities = set()
    for office in map_data["labor_offices"]:
        city = office["縣市別"].replace("辦事處", "").replace("市", "").replace("縣", "")
        cities.add(city)
    
    return {
        "cities": sorted(list(cities)),
        "success": True
    }

@app.post("/api/maps/nearby")
async def get_nearby_locations(request: NearbyLocationRequest):
    """獲取附近位置（含輸入驗證）"""
    try:
        logger.info(f"收到地圖搜索請求: lat={request.latitude}, lng={request.longitude}, type={request.type}, radius={request.radius}")
        
        if not map_data:
            logger.error("地圖數據未載入")
            raise DataLoadError("地圖數據載入失敗")
        
        # 計算距離並篩選附近的點
        nearby_locations = []
        
        if request.type == "hospital":
            import math
            
            # 計算真實距離（使用Haversine公式）
            def calculate_distance(lat1, lon1, lat2, lon2):
                R = 6371  # 地球半徑（公里）
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            
            # 按醫院等級分類
            hospital_categories = {
                "醫學中心": [],
                "區域醫院": [],
                "地區醫院": [],
                "診所": []
            }
            
            for hospital in map_data["hospitals"]:
                # 使用真實的經緯度
                hospital_lat = hospital.get("緯度")
                hospital_lng = hospital.get("經度")
                
                if hospital_lat is None or hospital_lng is None:
                    continue
                
                # 計算距離
                distance_km = calculate_distance(request.latitude, request.longitude, hospital_lat, hospital_lng)
                
                # 解析醫院等級
                level_text = hospital["醫院評鑑評鑑結果"]
                if "醫學中心" in level_text:
                    category = "醫學中心"
                elif "區域醫院" in level_text:
                    category = "區域醫院"
                elif "地區醫院" in level_text:
                    category = "地區醫院"
                else:
                    category = "診所"
                
                # 在醫院名稱後面加上等級標示
                hospital_name_with_level = f"{hospital['醫院名稱']}({category})"
                
                hospital_info = {
                    "name": hospital_name_with_level,
                    "original_name": hospital["醫院名稱"],  # 保留原始名稱
                    "address": hospital.get("地址", "地址不詳"),
                    "city": hospital["所在縣市"],
                    "type": "hospital",
                    "phone": hospital.get("醫院電話", ""),
                    "level": level_text,
                    "category": category,
                    "latitude": hospital_lat,
                    "longitude": hospital_lng,
                    "distance": round(distance_km, 2)
                }
                
                hospital_categories[category].append(hospital_info)
            
            # 按距離排序每個類別，並取最近的3個
            for category, hospitals in hospital_categories.items():
                hospitals.sort(key=lambda x: x["distance"])
                nearby_locations.extend(hospitals[:3])  # 每類取最近的3個
        elif request.type == "labor_office":
            logger.info(f"處理勞保局辦事處搜索，共有 {len(map_data['labor_offices'])} 個辦事處")
            # 簡化距離計算，直接返回所有勞保局辦事處
            for office in map_data["labor_offices"]:
                office_lat = float(office["緯度"])
                office_lng = float(office["經度"])
                
                # 簡單的距離計算
                lat_diff = request.latitude - office_lat
                lng_diff = request.longitude - office_lng
                distance_km = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
                
                nearby_locations.append({
                    "name": office["縣市別"],
                    "address": office["辦事處地址"],
                    "city": office["縣市別"],
                    "type": "labor_office",
                    "phone": office["辦事處電話"],
                    "service_hours": office["櫃台服務時間"],
                    "phone_hours": office["電話服務時間"],
                    "latitude": office_lat,
                    "longitude": office_lng,
                    "distance": distance_km
                })
            
            logger.info(f"勞保局辦事處處理完成，返回 {len(nearby_locations)} 個位置")
        
        # 按距離排序
        nearby_locations.sort(key=lambda x: x.get("distance", 0))
        
        # 根據類型限制返回數量
        if request.type == "hospital":
            # 醫院按等級分類返回（每類3個，共12個）
            result_locations = nearby_locations[:12]  # 最多12個（4類×3個）
            
            # 統計各類別數量
            category_counts = {}
            for location in result_locations:
                category = location.get("category", "未知")
                category_counts[category] = category_counts.get(category, 0) + 1
            
            result_message = f"找到最近的醫院：醫學中心{category_counts.get('醫學中心', 0)}家、區域醫院{category_counts.get('區域醫院', 0)}家、地區醫院{category_counts.get('地區醫院', 0)}家、診所{category_counts.get('診所', 0)}家"
        else:
            # 勞保局辦事處返回前20個
            result_locations = nearby_locations[:20]
            result_message = f"找到 {len(result_locations)} 個勞保局辦事處"
        
        return {
            "locations": result_locations,
            "total": len(nearby_locations),
            "message": result_message,
            "success": True
        }
    
    except DataLoadError as e:
        logger.error(f"地圖數據錯誤: {e}")
        return {"error": "地圖數據暫時無法使用", "success": False}
    except ValueError as e:
        logger.error(f"輸入驗證錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"獲取附近位置失敗: {traceback.format_exc()}")
        return {"error": "獲取附近位置失敗", "success": False}

@app.get("/api/maps/city/{city_name}")
async def get_locations_by_city(city_name: str, type: str = "hospital"):
    """根據城市獲取位置"""
    try:
        if not map_data:
            return {"error": "地圖數據載入失敗", "success": False}
        
        locations = []
        
        if type == "hospital":
            for hospital in map_data["hospitals"]:
                if city_name in hospital["所在縣市"]:
                    locations.append({
                        "name": hospital["醫院名稱"],
                        "address": hospital.get("地址", "地址不詳"),
                        "city": hospital["所在縣市"],
                        "type": "hospital",
                        "phone": hospital.get("電話", ""),
                        "level": hospital["醫院評鑑評鑑結果"],
                        "latitude": 25.0,  # 暫時使用預設值
                        "longitude": 121.5  # 暫時使用預設值
                    })
        elif type == "labor_office":
            for office in map_data["labor_offices"]:
                if city_name in office["縣市別"]:
                    locations.append({
                        "name": office["縣市別"],
                        "address": office["辦事處地址"],
                        "city": office["縣市別"],
                        "type": "labor_office",
                        "phone": office["辦事處電話"],
                        "service_hours": office["櫃台服務時間"],
                        "phone_hours": office["電話服務時間"],
                        "latitude": float(office["緯度"]),
                        "longitude": float(office["經度"])
                    })
        
        return {
            "locations": locations,
            "city": city_name,
            "type": type,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"獲取城市位置失敗: {e}")
        return {"error": "獲取城市位置失敗", "success": False}

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🏥 啟動勞資屬道山服務 v2.1（第二階段優化版）")
    print("=" * 60)
    print(f"🌐 API 服務: http://localhost:{Config.API_PORT}")
    print(f"🌐 API 服務: http://127.0.0.1:{Config.API_PORT}")
    print(f"📖 API 文檔: http://localhost:{Config.API_PORT}/docs")
    print(f"🤖 AI 模型: {Config.OLLAMA_MODEL}")
    print(f"💾 資料目錄: {Config.DATA_DIR}")
    print(f"📝 日誌目錄: {log_dir}")
    print("=" * 60)
    print("\n✅ 第一階段優化:")
    print("  • 配置集中管理")
    print("  • LRU 快取機制")
    print("  • 完善錯誤處理")
    print("  • Pydantic 輸入驗證")
    print("  • 相似度閾值過濾")
    print("\n⚡ 第二階段優化:")
    print("  • 非同步處理（ThreadPoolExecutor）")
    print("  • 批次資料載入")
    print("  • API 速率限制（20次/分鐘）")
    print("  • 日誌輪替系統（10MB，5個備份）")
    print("=" * 60)
    
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT, log_level="info")
