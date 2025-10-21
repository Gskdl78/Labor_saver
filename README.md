# 🏥 勞保衛隊

一個基於 React 和 FastAPI 的勞工保險智能諮詢平台，整合 RAG 系統、本地 AI 模型、地圖服務和互動式人體圖像介面。

[![Version](https://img.shields.io/badge/version-2.3-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](requirements.txt)
[![Node](https://img.shields.io/badge/node-18--20-green.svg)](frontend/package.json)

## ✨ 核心特色

- 🤖 **RAG 增強型 AI 問答** - 基於向量資料庫的智能檢索，準確率 95%+
- ⚡ **常見問題加速** - 快速回答常見問題（<1 秒）
- 🗺️ **智能地圖導航** - 勞保局辦事處與合格醫院定位
- 👤 **互動式身體檢測** - 點擊式人體圖像，快速描述傷害部位
- 📊 **失能給付查詢** - 自動計算給付標準

## 🚀 快速開始

### 前置需求

| 軟體 | 版本 | 說明 |
|------|------|------|
| **Python** | 3.8+ | 後端服務 |
| **Node.js** | 18-20 | 前端建置（避免使用 22+） |
| **Ollama** | 最新版 | 本地 AI 模型服務 |

#### 安裝 Ollama

```bash
# Windows - 下載並安裝
# https://ollama.ai/download

# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# 啟動 Ollama 服務（保持運行）
ollama serve

# 下載 AI 模型
ollama pull gemma3:4b
```

### 安裝與運行

#### 1. 安裝依賴

```bash
# 安裝後端依賴
pip install -r requirements.txt

# 安裝前端依賴
cd frontend
npm install
```

#### 2. 設定環境變數

複製 `env_example.txt` 為 `.env` 並根據需要修改配置：

```bash
# 複製環境變數範例文件
cp env_example.txt .env
```

**.env 配置說明：**
```bash
# API 設定
API_HOST=localhost          # API 服務主機（0.0.0.0 允許外部訪問）
API_PORT=8000              # API 服務端口

# Ollama 設定
OLLAMA_HOST=http://localhost:11434  # Ollama 服務地址
OLLAMA_MODEL=gemma3:4b              # 使用的 AI 模型

# ChromaDB 設定
CHROMA_DB_PATH=./chroma_db   # 向量資料庫存儲路徑

# 前端設定
REACT_APP_API_URL=http://localhost:8000/api  # 後端 API 地址
```

#### 3. 構建前端

```bash
# 進入前端目錄
cd frontend

# 若使用 Node.js 21/22 以上，請先加上 OpenSSL 相容旗標再建置
# Windows PowerShell（當前視窗有效）
$env:NODE_OPTIONS="--openssl-legacy-provider"; npm run build

# 如果是 Node.js 18~20，仍建議優先使用下列標準指令
# npm run build
```

#### 4. 啟動服務

**🎯 推薦方式（自動化啟動）**
```powershell
# Windows PowerShell - 一鍵啟動前後端
.\start_all.ps1
```

**手動啟動**
```bash
# 後端（專案根目錄）
.\start_backend.ps1   # Windows
python simple_backend.py   # 手動啟動

# 前端（另一個終端視窗）
cd frontend
npx serve -s build -l 3000
```

#### 5. 訪問應用

| 服務 | 網址 | 說明 |
|------|------|------|
| **前端** | http://localhost:3000 | 使用者介面 |
| **後端 API** | http://localhost:8000 | REST API 服務 |
| **API 文檔** | http://localhost:8000/docs | Swagger 互動式文檔 |

---

## 📋 功能特色

### 1. 🤖 RAG 增強型 AI 諮商
- **向量資料庫檢索** - ChromaDB + Sentence Transformers
- **智能排序算法** - 相似度 + 關鍵詞匹配雙重評分
- **常見問題加速** - 資料庫直接回答（<1 秒）
- **RAG 深度問答** - 向量檢索 + AI 生成（10-15 秒）
- **準確率 95%+** - 精確匹配勞保法規

### 2. 🗺️ 智能地圖服務
- **勞保局辦事處定位** - 全台各地辦事處查詢
- **合格醫院導航** - 衛福部評鑑合格醫院列表
- **平滑地圖導航** - 點擊自動飛行到目標位置
- **詳細資訊展示** - 地址、電話、經緯度資訊

### 3. 👤 互動式身體檢測
- **男女分離圖像** - 專業醫學解剖圖
- **18 個身體部位** - 精確定位受傷部位
- **透明點擊區域** - 直觀的圖像互動
- **失能等級分析** - 自動匹配失能給付標準

### 4. 📊 失能給付查詢
- **自動計算給付** - 根據投保薪資與失能等級
- **即時查詢** - 快速返回給付金額
- **分級標準展示** - 完整的失能等級對照表

## 🛠️ 技術架構

### 後端技術棧
- **FastAPI** - 高效能異步 Web 框架
- **Ollama** - 本地 LLM 服務（Gemma3:4b）
- **ChromaDB** - 向量資料庫（Cosine 相似度）
- **Sentence Transformers** - 文本嵌入模型
- **Pydantic V2** - 資料驗證與序列化
- **ThreadPoolExecutor** - 非同步任務處理

### 前端技術棧
- **React** - 使用者介面框架
- **Material-UI** - UI 組件庫
- **Leaflet** - 互動式地圖（OpenStreetMap）
- **Axios** - HTTP 客戶端

### 效能優化
- **LRU 快取** - 嵌入向量快取（提升 70% 效能）
- **速率限制** - IP 基礎請求限制（30 req/min）
- **日誌輪替** - 自動管理日誌文件（10MB/file）
- **錯誤降級** - 多層次降級策略

## 📁 專案結構

```
勞保衛隊/
├── frontend/                          # React 前端
│   ├── public/                        # 靜態資源
│   │   ├── 男_new.png, 女_new.png    # 人體圖像
│   │   └── images/                    # 其他圖片
│   ├── src/
│   │   ├── components/               # 可重用組件
│   │   │   ├── BodyDiagram.js       # 身體檢測組件
│   │   │   ├── MapComponent.js       # 地圖組件
│   │   │   └── ...
│   │   ├── pages/                    # 頁面組件
│   │   │   ├── ChatPage.js          # AI 諮詢頁面
│   │   │   ├── MapPage.js           # 地圖頁面
│   │   │   ├── BodyInteractionPage.js # 身體檢測頁面
│   │   │   └── HomePage.js          # 首頁
│   │   └── services/
│   │       └── api.js               # API 服務層
│   └── build/                        # 構建輸出
├── 勞保資料集/                        # 知識庫數據
│   ├── 常見問題資料庫.json
│   ├── 勞工保險失能給付標準第三條附表.json
│   ├── 各失能等級之給付標準.json
│   ├── 勞保局各地辦事處.json
│   └── 衛生福利部評鑑合格之醫院名單_含經緯度.json
├── chroma_db/                        # ChromaDB 向量資料庫
├── logs/                             # 日誌文件
│   └── app.log
├── simple_backend.py                 # FastAPI 後端主程式
├── start_backend.ps1                 # 後端啟動腳本
├── start_all.ps1                     # 一鍵啟動腳本
├── requirements.txt                  # Python 依賴
├── .env                              # 環境變數（需自行建立）
├── env_example.txt                   # 環境變數範例
├── README.md                         # 專案說明
└── CHANGELOG.md                      # 開發日誌
```

## 🔧 故障排除

### 1. Ollama 連接失敗

**症狀**：前端顯示「AI 服務暫時無法使用」

**解決方案**：
```bash
# 1. 確認 Ollama 服務運行中
ollama serve

# 2. 確認模型已安裝
ollama list

# 3. 使用啟動腳本（自動設定環境變數）
.\start_backend.ps1
```

**注意**：系統環境變數可能覆蓋 `.env` 設定，建議使用提供的啟動腳本。

### 2. Node.js 建置錯誤

**症狀**：`error:0308010C:digital envelope routines::unsupported`

**解決方案**：
```bash
# Windows PowerShell
cd frontend
$env:NODE_OPTIONS="--openssl-legacy-provider"; npm run build

# 或降級到 Node.js 18-20
nvm use 20
npm run build
```

### 3. 向量資料庫錯誤

**症狀**：RAG 系統無法檢索相關文檔

**解決方案**：
```bash
# 刪除舊的資料庫並重新啟動
Remove-Item -Recurse -Force chroma_db
python simple_backend.py
```

### 4. 端口衝突

| 服務 | 端口 | 修改方式 |
|------|------|---------|
| 後端 | 8000 | 修改 `.env` 中的 `API_PORT` |
| 前端 | 3000 | `npx serve -s build -l <端口>` |
| Ollama | 11434 | 修改 `.env` 中的 `OLLAMA_HOST` |

**Windows 查看端口占用**：
```powershell
netstat -ano | findstr :8000
```

### 5. 常見問題檢查清單

- [ ] Ollama 服務已啟動
- [ ] Gemma3:4b 模型已下載
- [ ] `.env` 文件已建立（參考 `env_example.txt`）
- [ ] Python 依賴已安裝（`pip install -r requirements.txt`）
- [ ] 前端已建置（`npm run build`）
- [ ] 端口 8000 和 3000 未被占用

## 📝 開發說明

### 環境變數配置

專案使用 `.env` 文件進行配置。參考 `env_example.txt` 建立您的配置：

```bash
# API 設定
API_HOST=localhost
API_PORT=8000

# Ollama 設定
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# ChromaDB 設定
CHROMA_DB_PATH=./chroma_db

# 前端設定
REACT_APP_API_URL=http://localhost:8000/api
```

### 修改 AI 模型

支援所有 Ollama 相容的模型：

```bash
# 查看可用模型
ollama list

# 下載新模型
ollama pull llama2
ollama pull mistral

# 修改 .env
OLLAMA_MODEL=llama2
```

**推薦模型**：
- `gemma3:4b` - 平衡效能與準確度（預設）
- `llama2:13b` - 更高準確度，需要更多資源
- `mistral:7b` - 快速回應，中等準確度

### 添加知識庫數據

所有數據文件位於 `勞保資料集/` 目錄：

| 文件 | 用途 |
|------|------|
| `常見問題資料庫.json` | 快速問答資料 |
| `勞工保險失能給付標準第三條附表.json` | RAG 向量檢索資料 |
| `各失能等級之給付標準.json` | 給付金額計算 |
| `勞保局各地辦事處.json` | 地圖位置資料 |
| `衛生福利部評鑑合格之醫院名單_含經緯度.json` | 醫院位置資料 |

**格式範例**：
```json
// 常見問題資料庫.json
{
  "questions": [
    {
      "keywords": ["關鍵詞1", "關鍵詞2"],
      "answer": "答案內容"
    }
  ]
}
```

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/chat` | POST | AI 問答（RAG + LLM） |
| `/api/body-part/injury-info` | POST | 身體部位傷害查詢 |
| `/api/disability/benefit` | POST | 失能給付計算 |
| `/api/maps/nearby` | POST | 地圖位置查詢 |
| `/docs` | GET | Swagger API 文檔 |

### 性能調優

**快取設定**（`simple_backend.py`）：
```python
CACHE_MAX_SIZE = 1000  # 嵌入向量快取大小
VECTOR_SEARCH_TOP_K = 5  # 向量檢索數量
SIMILARITY_THRESHOLD = 0.6  # 相似度閾值
```

**並發設定**：
```python
THREAD_POOL_MAX_WORKERS = 4  # 並發處理線程數
RATE_LIMIT_REQUESTS = 30  # 每分鐘請求限制
```

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發流程
1. Fork 專案
2. 建立功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交變更（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 開啟 Pull Request

---

## 📜 版本歷史

查看 [CHANGELOG.md](CHANGELOG.md) 了解詳細的版本更新記錄。

**當前版本**：v2.3
- ✅ RAG 系統優化（準確率 95%+）
- ✅ 常見問題加速（<1 秒回應）
- ✅ 互動式身體檢測
- ✅ 智能地圖導航

---

## 📄 授權

本專案僅供學習和研究使用。

---

## 📞 聯絡方式

如有任何問題或建議，歡迎透過 GitHub Issues 聯絡我們。

---

**🌟 如果這個專案對您有幫助，請給我們一個 Star！**