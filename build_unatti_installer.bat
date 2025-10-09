@echo off
title Unatti Bank Reconciliation Tool - Build Script
color 0A

echo ================================================================
echo    UNATTI BANK RECONCILIATION TOOL - BUILD SCRIPT
echo    Developed by: Neuro Spark Work Solutions
echo    Client: Unatti Finserv
echo ================================================================
echo.

REM Clean previous builds
echo [Step 1] Cleaning previous builds...
if exist "installer_output" (
    rmdir /s /q "installer_output"
    echo ✓ Cleaned installer output
)
if exist "dist" (
    rmdir /s /q "dist" 
    echo ✓ Cleaned distribution files
)
if exist "build" (
    rmdir /s /q "build"
    echo ✓ Cleaned build files
)

echo.
echo [Step 2] Creating fast executable (--onedir)...
echo Building: BankReconciliationTool.exe

REM Create the executable using onedir for fast startup
pyinstaller --onedir --windowed --icon=assets\bank_icon.ico --name="BankReconciliationTool" --add-data="src;src" src/main_modular.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Failed to create executable
    echo Please check that:
    echo   • Python and PyInstaller are installed
    echo   • All dependencies are available
    echo   • assets\bank_icon.ico exists
    echo.
    pause
    exit /b 1
)

echo ✓ Executable created successfully

echo.
echo [Step 3] Building Unatti installer...
echo Using Inno Setup to create professional installer...

REM Build the installer using Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer_files\setup.iss"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Failed to create installer
    echo Please check that:
    echo   • Inno Setup 6 is installed
    echo   • setup.iss file exists in installer_files\
    echo   • All source files are available
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    BUILD COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo 📁 FILES CREATED:
echo    Executable: dist\BankReconciliationTool\BankReconciliationTool.exe
echo    Installer:  installer_output\Unatti_BankReconciliationTool_Setup_v1.0.0.exe
echo.
echo 🚀 FEATURES:
echo    ✓ Fast startup (2-3 seconds with --onedir)
echo    ✓ Professional Windows installer
echo    ✓ Unatti branding and customization
echo    ✓ Start menu integration
echo    ✓ Desktop shortcut option
echo    ✓ Proper uninstall process
echo.
echo 📧 SUPPORT: vinod@neurosparkworks.com
echo 🏢 CLIENT: Unatti Finserv
echo 💻 DEVELOPER: Neuro Spark Work Solutions
echo.
echo The installer is ready for distribution to Unatti Finserv!
echo.
pause