@echo off
echo ============================================
echo   YTWERSE - Build Script
echo ============================================
echo.

:: Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if %errorlevel% neq 0 (
    echo [!] PyInstaller nao encontrado. Instalando...
    pip install pyinstaller
)

:: Check if pywebview is installed
python -c "import webview" 2>NUL
if %errorlevel% neq 0 (
    echo [!] pywebview nao encontrado. Instalando...
    pip install pywebview
)

echo [1] Limpando builds anteriores...
if exist "dist\YTWERSE.exe" del /f /q "dist\YTWERSE.exe"
if exist "build" rmdir /s /q "build"

echo [2] Compilando YTWERSE.exe...
pyinstaller ytwerse.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Build falhou! Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build concluido com sucesso!
echo   Arquivo: dist\YTWERSE.exe
echo ============================================
echo.
pause
