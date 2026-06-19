# UBY Specification GitHub Upload Script (PowerShell)
Write-Host "========================================" -ForegroundColor Green
Write-Host "UBY Specification GitHub Upload Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取GitHub用户名
$USERNAME = Read-Host "请输入您的GitHub用户名"

Write-Host ""
Write-Host "正在为用户 $USERNAME 准备上传命令..." -ForegroundColor Yellow
Write-Host ""

Write-Host "1. 请先在GitHub上创建仓库:" -ForegroundColor Cyan
Write-Host "   - 访问 https://github.com/new" -ForegroundColor White
Write-Host "   - 仓库名称: UBY-Specification" -ForegroundColor White
Write-Host "   - 描述: UBY Cross-scale Time Labeling Specification v0.1.0" -ForegroundColor White
Write-Host "   - 设为公开仓库" -ForegroundColor White
Write-Host "   - 不要添加README、.gitignore或许可证（我们已经有了）" -ForegroundColor White
Write-Host ""

Read-Host "创建完仓库后，按Enter继续"

Write-Host "2. 正在添加远程仓库..." -ForegroundColor Yellow
git remote add origin "https://github.com/$USERNAME/UBY-Specification.git"

Write-Host "3. 正在重命名主分支为main..." -ForegroundColor Yellow
git branch -M main

Write-Host "4. 正在推送代码到GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "5. 正在推送版本标签..." -ForegroundColor Yellow
git push origin v0.1.0

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "请访问: https://github.com/$USERNAME/UBY-Specification" -ForegroundColor Cyan
Write-Host "验证所有文件都已正确上传。" -ForegroundColor White
Write-Host ""

Write-Host "建议下一步:" -ForegroundColor Yellow
Write-Host "1. 在GitHub上创建v0.1.0发布版本" -ForegroundColor White
Write-Host "2. 连接Zenodo获得DOI" -ForegroundColor White
Write-Host ""

Read-Host "按Enter退出"
