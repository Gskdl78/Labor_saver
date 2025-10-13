# 勞資屬道山

一個基於React和FastAPI的勞資屬道山諮詢平台，整合本地語言模型、地圖服務和圖像式互動介面。

## 🚀 快速開始

### 前置需求

1. **Python 3.8+**
2. **Node.js 18-20** (避免使用 Node.js 22+ 以免出現兼容性問題)
3. **Ollama** - 用於運行本地 LLM
   ```bash
   # 安裝 Ollama (Windows)
   # 下載並安裝：https://ollama.ai/download

   # 安裝 Ollama (Linux/Mac)
   curl -fsSL https://ollama.ai/install.sh | sh

   # 啟動 Ollama 服務 (在第一個命令提示字元視窗)
   ollama serve

   # 下載 Gemma 模型 (在第二個命令提示字元視窗)
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

**啟動後端** (在專案根目錄)：
```bash
python simple_backend.py
```

**啟動前端** (在 frontend 目錄)：
```bash
npx serve -s build -l 3000
```

#### 5. 訪問應用

- 前端：http://localhost:3000
- 後端API：http://localhost:8000
- API文檔：http://localhost:8000/docs

## 📋 功能特色

### 1. 語言模型諮商
- 基於 Ollama Gemma3 4B 模型的智能諮詢
- 常見問題快速回答
- 勞工保險相關問題專業解答

### 2. 地圖搜索
- 勞保局辦事處位置查詢
- 合格醫院推薦
- 基於用戶位置的智能推薦

### 3. 圖像式互動介面
- 點擊人體部位圖進行傷害描述
- 失能等級智能分析
- 給付標準查詢

## 🛠️ 技術架構

- **前端**: React + Material-UI
- **後端**: FastAPI + Python
- **AI模型**: Ollama Gemma3 4B
- **地圖服務**: OpenStreetMap + Leaflet
- **數據存儲**: JSON 文件 + ChromaDB

## 📁 專案結構

```
勞保衛隊/
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/      # 組件
│   │   ├── pages/          # 頁面
│   │   └── services/       # API 服務
│   └── build/              # 構建輸出
├── backend/                 # FastAPI 後端 (未使用)
├── 勞保資料集/              # 數據文件
├── simple_backend.py       # 主後端服務
├── requirements.txt        # Python 依賴
└── README.md              # 說明文檔
```

## 🔧 故障排除

### Node.js 兼容性問題
如果遇到 `error:0308010C:digital envelope routines::unsupported` 錯誤（常見於 Node.js 21/22+）：
```bash
# 進入前端目錄
cd frontend

# Windows PowerShell（當前視窗有效）
$env:NODE_OPTIONS="--openssl-legacy-provider"; npm run build

# 建置完成後啟動靜態服務
npx serve -s build -l 3000
```
若希望長期固定此設定（不建議於全域環境），可以在 PowerShell 以系統層級設定：
```powershell
setx NODE_OPTIONS "--openssl-legacy-provider"
```
或改用 Node.js 18~20 版本以避免此相容性問題。

### Ollama 連接問題
確保 Ollama 服務正在運行：
```bash
ollama serve
ollama list  # 確認 gemma3:4b 已安裝
```

### 端口衝突
- 後端默認端口：8000（可在 `.env` 中修改 `API_PORT`）
- 前端默認端口：3000（使用 `npx serve -s build -l <端口>` 修改）
- 如遇端口衝突，請終止占用進程或通過 `.env` 文件修改配置

## 📝 開發說明

### 環境變數配置
專案使用 `.env` 文件進行配置，所有主要設定都可以通過環境變數調整，無需修改程式碼。

### 修改 AI 模型
如需使用其他 Ollama 模型，請修改 `.env` 文件中的 `OLLAMA_MODEL` 設定：
```bash
# .env 文件
OLLAMA_MODEL=gemma3:4b  # 修改為您的模型名稱，例如：llama2、mistral 等
```

可用的模型可以通過以下命令查看：
```bash
ollama list  # 查看已安裝的模型
ollama pull <模型名稱>  # 下載新模型
```

### 修改 API 端口
如需修改 API 端口或主機地址，請在 `.env` 文件中調整：
```bash
API_HOST=0.0.0.0  # 設定為 0.0.0.0 允許外部訪問
API_PORT=8000     # 修改為您想要的端口
```

**注意**：修改後端 API 地址後，也需要同步更新前端的 `REACT_APP_API_URL` 設定。

### 添加數據
- 勞保局辦事處：`勞保資料集/勞保局各地辦事處.json`
- 醫院名單：`勞保資料集/衛生福利部評鑑合格之醫院名單.json`
- 失能給付標準：`勞保資料集/各失能等級之給付標準.json`

## 📄 授權

本專案僅供學習和研究使用。