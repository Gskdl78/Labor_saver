# 勞保衛隊後端啟動腳本
Write-Host "=" -ForegroundColor Cyan
Write-Host "🏥 正在啟動勞保衛隊後端服務..." -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

# 設置正確的環境變數
$env:OLLAMA_HOST="http://localhost:11434"
$env:OLLAMA_MODEL="gemma3:4b"
$env:API_HOST="0.0.0.0"
$env:API_PORT="8000"
$env:CHROMA_DB_PATH="./chroma_db"

Write-Host "✅ 環境變數已配置：" -ForegroundColor Green
Write-Host "   OLLAMA_HOST = $env:OLLAMA_HOST"
Write-Host "   OLLAMA_MODEL = $env:OLLAMA_MODEL"
Write-Host ""

# 啟動後端
python simple_backend.py

