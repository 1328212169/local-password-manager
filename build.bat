@echo off
chcp 65001 >nul
echo ========================================
echo 密码管理器 v1.2.3 打包脚本
echo ========================================
echo.

REM 清理旧的构建文件
echo [1/4] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "密码管理器.spec" del /q "密码管理器.spec"
echo 清理完成
echo.

REM 使用 PyInstaller 打包
echo [2/4] 开始打包...
pyinstaller --name="密码管理器" ^
    --windowed ^
    --onefile ^
    --icon=NONE ^
    --version-file=version_info.txt ^
    --add-data="requirements.txt;." ^
    --add-data="README.md;." ^
    --add-data="CHANGELOG.md;." ^
    --hidden-import=PyQt6 ^
    --hidden-import=argon2 ^
    --hidden-import=cryptography ^
    --clean ^
    main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 打包完成，创建压缩包...

REM 复制发布说明到dist目录
if exist "发布说明.txt" copy /Y "发布说明.txt" "dist\发布说明.txt"

REM 创建压缩包
cd dist
powershell -Command "Compress-Archive -Path '密码管理器.exe','发布说明.txt' -DestinationPath '密码管理器1.2.3.zip' -Force"
cd ..

echo.
echo [4/4] 压缩包创建完成
echo.
echo ========================================
echo 打包成功！
echo 可执行文件位置: dist\密码管理器.exe
echo 压缩包位置: dist\密码管理器1.2.3.zip
echo ========================================
echo.
pause
