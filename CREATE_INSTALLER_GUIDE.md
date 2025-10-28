# Creating a Windows Installer for Bank Reconciliation Tool

## Method 1: Using Inno Setup (Recommended - Professional Installer)

### Step 1: Install Inno Setup
1. Download Inno Setup from: https://jrsoftware.org/isdl.php
2. Install Inno Setup on your computer

### Step 2: Build the EXE with PyInstaller
```powershell
# Make sure you're in the project directory
cd "E:\BANK RECON\BankReconsilation"

# Build the executable with icon
pyinstaller BankReconciliationTool.spec
```

### Step 3: Create Inno Setup Script
1. Open Inno Setup
2. Use the "Script Wizard" or use the provided script (see `installer_script.iss`)
3. Configure:
   - Application name: Bank Reconciliation Tool
   - Version: 1.0.0
   - Publisher: Your Company Name
   - Application folder: dist/BankReconciliationTool (from PyInstaller)
   - Output folder: installers/

### Step 4: Compile the Installer
1. Open `installer_script.iss` in Inno Setup
2. Click "Build" → "Compile"
3. The installer will be created in the `installers/` folder

---

## Method 2: Using NSIS (Nullsoft Scriptable Install System)

### Step 1: Install NSIS
1. Download from: https://nsis.sourceforge.io/Download
2. Install NSIS

### Step 2: Create NSIS Script
Use the provided `installer_script.nsi` file

### Step 3: Compile
1. Right-click on `installer_script.nsi`
2. Select "Compile NSIS Script"

---

## Method 3: Using Auto PY to EXE (Easiest - GUI Based)

### Step 1: Install Auto PY to EXE
```powershell
pip install auto-py-to-exe
```

### Step 2: Launch GUI
```powershell
auto-py-to-exe
```

### Step 3: Configure Settings
- Script Location: `src/main_modular.py`
- Onefile: One Directory
- Console Window: Window Based (hide the console)
- Icon: Select `assets/logo.ico`
- Additional Files: Add any data files if needed

### Step 4: Convert
Click "Convert .py to .exe"

---

## Adding Logo/Icon

### Option 1: During PyInstaller Build
Edit `BankReconciliationTool.spec` and add icon parameter:
```python
exe = EXE(
    ...
    name='BankReconciliationTool',
    icon='assets/logo.ico',  # Add this line
    ...
)
```

### Option 2: Using Resource Hacker (After Build)
1. Download Resource Hacker: http://www.angusj.com/resourcehacker/
2. Open your .exe file
3. Replace icon resources
4. Save

---

## Quick Build Commands

### Build with Icon:
```powershell
# Update spec file first, then:
pyinstaller BankReconciliationTool.spec
```

### Build Single File with Icon:
```powershell
pyinstaller --onefile --windowed --icon=assets/logo.ico --name="BankReconciliationTool" src/main_modular.py
```

---

## Logo Requirements

### For Windows EXE Icon:
- Format: `.ico` file
- Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- Can convert PNG to ICO using online tools or tools like:
  - ImageMagick: `magick convert logo.png -define icon:auto-resize=256,128,64,48,32,16 logo.ico`
  - Online: https://convertio.co/png-ico/

### For Application Window:
- Format: `.png` or `.ico`
- Recommended size: 256x256 or 512x512

---

## Installer Features to Include

✅ Custom installation directory
✅ Desktop shortcut creation
✅ Start menu entry
✅ Uninstaller
✅ File associations (optional)
✅ Launch on finish option
✅ Custom license agreement
✅ Custom images/banners
✅ Version checking
✅ Silent install option

---

## Testing Checklist

- [ ] Install on clean Windows machine
- [ ] Test all features work
- [ ] Test uninstall removes everything
- [ ] Check desktop shortcut works
- [ ] Check start menu entry works
- [ ] Verify icon displays correctly
- [ ] Test with different Windows versions (10, 11)
- [ ] Check antivirus doesn't flag it
