@echo off
REM Build Script for Bank Reconciliation Tool

echo ========================================
echo Bank Reconciliation Tool - Build Script
echo ========================================
echo.

REM Step 1: Check for logo
if not exist "assets\logo.ico" (
    echo [STEP 1] Creating logo...
    echo Installing Pillow if needed...
    pip install pillow
    python create_logo.py
    echo.
) else (
    echo [STEP 1] Logo already exists - skipping
    echo.
)

REM Step 2: Install dependencies
echo [STEP 2] Installing/updating dependencies...
pip install -r requirements.txt
pip install pyinstaller xlsxwriter openpyxl pillow
echo.

REM Step 3: Clean previous builds
echo [STEP 3] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo.

REM Step 4: Build executable
echo [STEP 4] Building executable with PyInstaller...
pyinstaller BankReconciliationTool.spec
echo.

REM Step 5: Check if build succeeded
if exist "dist\BankReconciliationTool\BankReconciliationTool.exe" (
    echo ========================================
    echo ✅ BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable location: dist\BankReconciliationTool\BankReconciliationTool.exe
    echo.
    echo Next steps:
    echo   1. Test the application: cd dist\BankReconciliationTool ^&^& BankReconciliationTool.exe
    echo   2. Create installer: Open installer_script.iss in Inno Setup and compile
    echo.
    
    REM Ask if user wants to run the app
    set /p run="Do you want to run the application now? (y/n): "
    if /i "%run%"=="y" (
        start "" "dist\BankReconciliationTool\BankReconciliationTool.exe"
    )
) else (
    echo ========================================
    echo ❌ BUILD FAILED!
    echo ========================================
    echo Please check the error messages above.
)

pause
