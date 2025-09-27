# 智慧勞災保險一站式服務

一個基於React和FastAPI的智慧勞災保險諮詢平台，整合本地語言模型、地圖服務和圖像式互動介面。

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

#### 2. 構建前端

```bash
cd frontend
npm run build
```

#### 3. 啟動服務

**啟動後端** (在專案根目錄)：
```bash
python simple_backend.py
```

**啟動前端** (在 frontend 目錄)：
```bash
npx serve -s build -l 3000
```

#### 4. 訪問應用

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
如果遇到 `error:0308010C:digital envelope routines::unsupported` 錯誤：
```bash
# 使用生產構建模式
cd frontend
npm run build
npx serve -s build -l 3000
```

### Ollama 連接問題
確保 Ollama 服務正在運行：
```bash
ollama serve
ollama list  # 確認 gemma3:4b 已安裝
```

### 端口衝突
- 後端默認端口：8000
- 前端默認端口：3000
- 如遇端口衝突，請終止占用進程或修改配置

## 📝 開發說明

### 修改模型
如需使用其他 Ollama 模型，請修改 `simple_backend.py` 中的模型名稱：
```python
# 第 137 行附近
model="gemma3:4b"  # 修改為您的模型名稱
```

### 添加數據
- 勞保局辦事處：`勞保資料集/勞保局各地辦事處.json`
- 醫院名單：`勞保資料集/衛生福利部評鑑合格之醫院名單.json`
- 失能給付標準：`勞保資料集/各失能等級之給付標準.json`

## 📄 授權

本專案僅供學習和研究使用。