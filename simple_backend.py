#!/usr/bin/env python3
"""修復版後端服務"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import logging
import ollama

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="智慧勞災保險一站式服務",
    description="提供勞災保險諮詢、地圖搜索和失能給付查詢服務",
    version="1.0.0"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:61269", "http://127.0.0.1:3000", "http://127.0.0.1:61269"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# 載入常見問題資料庫
def load_qa_database():
    """載入常見問題資料庫"""
    try:
        with open('常見問題資料庫.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("常見問題資料庫文件不存在，使用預設問題")
        return None
    except Exception as e:
        logger.error(f"載入常見問題資料庫失敗: {e}")
        return None

# 載入常見問題資料庫
qa_database = load_qa_database()

# 初始化 Ollama 客戶端
ollama_client = ollama.Client(host='http://127.0.0.1:11434')

# 請求模型
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    success: bool

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
    return {"message": "智慧勞災保險一站式服務 API"}

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """優化版聊天 API"""
    try:
        # 1. 先檢查是否有預設答案
        preset_answer = find_preset_answer(request.message)
        if preset_answer and preset_answer.strip():
            return ChatResponse(
                response=preset_answer,
                sources=["預設知識庫"],
                success=True
            )
        
        # 2. 如果沒有預設答案，使用語言模型（限制50字）
        prompt = f"""你是勞災保險諮詢助手，專門回答勞工保險相關問題。

問題：{request.message}

請用繁體中文簡潔回答，限制在50字以內，提供準確的資訊："""

        # 使用 Ollama 生成回答
        response = ollama_client.generate(
            model="gemma3:4b",
            prompt=prompt,
            options={
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 100,  # 減少token數，加快響應
            }
        )
        
        # 限制回答長度在50字內
        answer = response['response'].strip()
        if len(answer) > 50:
            answer = answer[:47] + "..."
        
        return ChatResponse(
            response=answer,
            sources=["AI 語言模型"],
            success=True
        )
        
    except Exception as e:
        logger.error(f"聊天處理失敗: {e}")
        return ChatResponse(
            response="抱歉，處理您的問題時發生錯誤，請稍後再試。",
            sources=[],
            success=False
        )

@app.post("/api/disability/body-part")
async def analyze_body_part_injury(request: dict):
    """根據身體部位和傷害描述分析可能的失能等級"""
    try:
        body_part = request.get("body_part", "")
        injury_description = request.get("injury_description", "")
        
        if not body_part or not injury_description:
            return {
                "error": "請提供身體部位和傷害描述",
                "success": False
            }
        
        # 構建分析提示詞
        prompt = f"""你是勞工保險失能給付標準專家。請根據以下資訊分析可能的失能等級：

身體部位：{body_part}
傷害描述：{injury_description}

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

        # 使用 Ollama 生成分析
        response = ollama_client.generate(
            model="gemma3:4b",
            prompt=prompt,
            options={
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 150,
            }
        )
        
        analysis = response['response'].strip()
        
        return {
            "body_part": body_part,
            "injury_description": injury_description,
            "analysis": analysis,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"身體部位分析失敗: {e}")
        return {
            "error": "分析身體部位傷害時發生錯誤",
            "success": False
        }

# 載入失能給付標準數據
def load_disability_benefit_standards():
    """載入失能給付標準數據"""
    try:
        with open('勞保資料集/各失能等級之給付標準.json', 'r', encoding='utf-8') as f:
            standards = json.load(f)
        return standards
    except Exception as e:
        logger.error(f"載入失能給付標準失敗: {e}")
        return None

# 載入失能給付標準
disability_standards = load_disability_benefit_standards()

@app.post("/api/disability/benefit")
async def get_disability_benefit(request: dict):
    """根據失能等級查詢給付標準"""
    try:
        level = request.get("level")
        injury_type = request.get("injury_type", "普通傷病")
        
        logger.info(f"查詢失能給付: level={level}, injury_type={injury_type}")
        
        if not level:
            return {"error": "請提供失能等級", "success": False}
        
        if not disability_standards:
            return {"error": "失能給付標準數據載入失敗", "success": False}
        
        # 從JSON數據中查找對應等級
        level_data = None
        for standard in disability_standards:
            if standard["失能等級"] == str(level):
                level_data = standard
                break
        
        if not level_data:
            return {"error": f"無效的失能等級: {level}", "success": False}
        
        # 提取給付日數
        ordinary_days = int(level_data["普通傷病失能補助費給付標準"].replace("日", ""))
        occupational_days = int(level_data["職業傷病失能補償費給付標準"].replace("日", ""))
        
        # 確定傷病類型
        if injury_type in ["職業傷病", "職業災害", "職業"]:
            benefit_type = "職業"
            benefit_days = occupational_days
        else:
            benefit_type = "普通"
            benefit_days = ordinary_days
        
        # 構建詳細說明
        level_int = int(level)
        severity = '較嚴重' if level_int <= 5 else '中等' if level_int <= 10 else '較輕微'
        
        explanation = f"""失能等級第{level}級給付標準：

給付日數：{benefit_days}日
傷病類型：{injury_type}
給付標準：{benefit_type}傷病

說明：
• 失能等級第{level}級屬於{severity}的失能程度
• 給付日數依勞工保險失能給付標準計算
• 職業傷病給付日數為普通傷病的1.5倍
• 實際給付金額需依投保薪資計算

注意事項：
• 需由健保特約醫院出具失能診斷書
• 申請時需檢附相關醫療證明文件
• 給付標準可能因法規修訂而調整"""
        
        return {
            "level": level,
            "injury_type": injury_type,
            "benefit_type": benefit_type,
            "benefit_days": benefit_days,
            "ordinary_days": ordinary_days,
            "occupational_days": occupational_days,
            "general_benefit": f"{ordinary_days}日",
            "occupational_benefit": f"{occupational_days}日",
            "explanation": explanation,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"查詢失能給付失敗: {e}")
        return {
            "error": "查詢失能給付時發生錯誤",
            "success": False
        }

# 載入地圖數據
def load_map_data():
    """載入地圖相關數據"""
    try:
        # 載入勞保局辦事處數據
        with open('勞保資料集/勞保局各地辦事處.json', 'r', encoding='utf-8') as f:
            labor_offices = json.load(f)
        
        # 載入醫院數據
        with open('勞保資料集/衛生福利部評鑑合格之醫院名單.json', 'r', encoding='utf-8') as f:
            hospitals = json.load(f)
        
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
async def get_nearby_locations(request: dict):
    """獲取附近位置"""
    try:
        latitude = request.get("latitude")
        longitude = request.get("longitude")
        location_type = request.get("type", "hospital")
        radius = request.get("radius", 50)
        
        logger.info(f"收到地圖搜索請求: lat={latitude}, lng={longitude}, type={location_type}, radius={radius}")
        
        if not latitude or not longitude:
            logger.error("缺少緯度或經度")
            return {"error": "請提供緯度和經度", "success": False}
        
        if not map_data:
            logger.error("地圖數據未載入")
            return {"error": "地圖數據載入失敗", "success": False}
        
        # 計算距離並篩選附近的點
        nearby_locations = []
        
        if location_type == "hospital":
            # 為醫院生成基於城市的座標
            city_coordinates = {
                "基隆市": (25.1276, 121.7395),
                "台北市": (25.0330, 121.5654),
                "新北市": (25.0169, 121.4628),
                "桃園市": (24.9936, 121.3010),
                "新竹市": (24.8066, 120.9686),
                "新竹縣": (24.8387, 121.0179),
                "苗栗縣": (24.5601, 120.8214),
                "台中市": (24.1477, 120.6736),
                "南投縣": (23.9605, 120.9718),
                "彰化縣": (24.0815, 120.5387),
                "雲林縣": (23.7081, 120.4313),
                "嘉義市": (23.4801, 120.4491),
                "嘉義縣": (23.4518, 120.2551),
                "台南市": (23.1417, 120.2513),
                "高雄市": (22.6273, 120.3014),
                "屏東縣": (22.6872, 120.4889),
                "宜蘭縣": (24.7021, 121.7377),
                "花蓮縣": (23.9739, 121.6014),
                "台東縣": (22.7603, 121.1479),
                "澎湖縣": (23.5711, 119.5794),
                "金門縣": (24.4327, 118.3171),
                "連江縣": (26.1608, 119.9492)
            }
            
            for hospital in map_data["hospitals"]:
                city = hospital["所在縣市"]
                if city in city_coordinates:
                    base_lat, base_lng = city_coordinates[city]
                    # 為同一城市的醫院添加小的隨機偏移
                    import random
                    random.seed(hash(hospital["醫院名稱"]))  # 使用醫院名稱作為種子，確保每次結果一致
                    lat_offset = random.uniform(-0.01, 0.01)
                    lng_offset = random.uniform(-0.01, 0.01)
                    
                    nearby_locations.append({
                        "name": hospital["醫院名稱"],
                        "address": hospital.get("地址", "地址不詳"),
                        "city": hospital["所在縣市"],
                        "type": "hospital",
                        "phone": hospital.get("醫院電話", ""),
                        "level": hospital["醫院評鑑評鑑結果"],
                        "latitude": base_lat + lat_offset,
                        "longitude": base_lng + lng_offset
                    })
        elif location_type == "labor_office":
            logger.info(f"處理勞保局辦事處搜索，共有 {len(map_data['labor_offices'])} 個辦事處")
            # 簡化距離計算，直接返回所有勞保局辦事處
            for office in map_data["labor_offices"]:
                office_lat = float(office["緯度"])
                office_lng = float(office["經度"])
                
                # 簡單的距離計算
                lat_diff = latitude - office_lat
                lng_diff = longitude - office_lng
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
        
        return {
            "locations": nearby_locations[:20],  # 限制返回數量
            "total": len(nearby_locations),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"獲取附近位置失敗: {e}")
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
    print("🏥 啟動智慧勞災保險服務...")
    print("🌐 API 服務: http://localhost:8000")
    print("🌐 API 服務: http://127.0.0.1:8000")
    print("📖 API 文檔: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
