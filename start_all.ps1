# 勞保衛隊前後端一鍵啟動腳本
Write-Host "=" -ForegroundColor Cyan
Write-Host "🚀 勞保衛隊服務啟動器" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

# 啟動後端（新視窗）
Write-Host "📡 正在啟動後端服務..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", ".\start_backend.ps1"

# 等待後端啟動
Write-Host "⏳ 等待後端啟動（8秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# 檢查後端健康狀態
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
    Write-Host "✅ 後端服務啟動成功！" -ForegroundColor Green
    Write-Host "   狀態: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  後端服務可能需要更多時間啟動" -ForegroundColor Yellow
}

Write-Host ""

# 啟動前端（新視窗）
Write-Host "🌐 正在啟動前端服務..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npx serve -s build -l 3000"

Write-Host ""
Write-Host "=" -ForegroundColor Cyan
Write-Host "✅ 服務啟動完成！" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 前端: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📡 後端: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 文檔: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Enter 關閉此視窗..." -ForegroundColor Gray
Read-Host

