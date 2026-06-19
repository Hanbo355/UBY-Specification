@echo off
echo ========================================
echo UBY Specification GitHub Upload Script
echo ========================================
echo.

REM 请将 YOUR_USERNAME 替换为您的实际GitHub用户名
set /p USERNAME="请输入您的GitHub用户名: "

echo.
echo 正在为用户 %USERNAME% 准备上传命令...
echo.

echo 1. 请先在GitHub上创建仓库:
echo    - 访问 https://github.com/new
echo    - 仓库名称: UBY-Specification
echo    - 描述: UBY Cross-scale Time Labeling Specification v0.1.0
echo    - 设为公开仓库
echo    - 不要添加README、.gitignore或许可证（我们已经有了）
echo.

pause

echo 2. 正在添加远程仓库...
git remote add origin https://github.com/%USERNAME%/UBY-Specification.git

echo 3. 正在重命名主分支为main...
git branch -M main

echo 4. 正在推送代码到GitHub...
git push -u origin main

echo 5. 正在推送版本标签...
git push origin v0.1.0

echo.
echo ========================================
echo 上传完成！
echo ========================================
echo.
echo 请访问: https://github.com/%USERNAME%/UBY-Specification
echo 验证所有文件都已正确上传。
echo.
echo 建议下一步:
echo 1. 在GitHub上创建v0.1.0发布版本
echo 2. 连接Zenodo获得DOI
echo.
pause
