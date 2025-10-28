# 🏦 Bank Reconciliation Tool - Installer & Logo Setup

## 📋 Quick Start Guide

### Option 1: Automatic Build (Recommended)
```powershell
# Just run this single command:
.\build.bat
```
This will:
- ✅ Create a logo automatically (if you don't have one)
- ✅ Install all dependencies
- ✅ Build the Windows executable
- ✅ Package everything into `dist/BankReconciliationTool/`

### Option 2: Manual Steps

#### Step 1: Create Logo (Optional)
```powershell
# Install Pillow first
pip install pillow

# Generate a simple logo
python create_logo.py
```

Or create your own logo and save as:
- `assets/logo.ico` - For Windows executable icon
- `assets/logo.png` - For application UI (optional)

#### Step 2: Build Executable
```powershell
# Install PyInstaller
pip install pyinstaller

# Build the app
pyinstaller BankReconciliationTool.spec
```

#### Step 3: Create Installer (Optional)
1. Download **Inno Setup**: https://jrsoftware.org/isdl.php
2. Install Inno Setup
3. Open `installer_script.iss` in Inno Setup
4. Click **Build** → **Compile**
5. Your installer will be in `installers/` folder

---

## 📁 Project Structure
```
BankReconsilation/
├── assets/                          # Logo and icons
│   ├── logo.ico                    # Windows executable icon
│   ├── logo.png                    # Application logo (optional)
│   └── README.md                   # Logo creation guide
├── src/                            # Source code
├── dist/                           # Built application (after build)
│   └── BankReconciliationTool/
│       └── BankReconciliationTool.exe
├── installers/                     # Installers (after Inno Setup)
│   └── BankReconciliationTool_Setup_v1.0.0.exe
├── BankReconciliationTool.spec     # PyInstaller configuration
├── installer_script.iss            # Inno Setup script
├── create_logo.py                  # Logo generator
├── build.bat                       # Automatic build script
└── CREATE_INSTALLER_GUIDE.md       # Detailed guide
```

---

## 🎨 Logo Customization

### Current Logo
The auto-generated logo shows "UF" with:
- Blue background (#4472C4)
- White text
- Green checkmark accent

### Create Your Own Logo

#### Requirements:
- **Icon file**: `assets/logo.ico`
  - Format: .ico with multiple sizes (16, 32, 48, 64, 128, 256)
  - Use for: Windows executable icon
  
- **PNG file**: `assets/logo.png` (optional)
  - Format: PNG with transparent background
  - Size: 256x256 or 512x512 pixels
  - Use for: Application UI

#### Tools to Create Logo:
1. **Online Converters**: 
   - PNG to ICO: https://convertio.co/png-ico/
   - Logo Maker: https://www.canva.com/

2. **Desktop Software**:
   - GIMP (free): https://www.gimp.org/
   - Photoshop
   - Illustrator

3. **Python Script** (included):
   ```powershell
   python create_logo.py
   ```

---

## 🚀 Building & Distribution

### Build Executable Only
```powershell
pyinstaller BankReconciliationTool.spec
```
Output: `dist/BankReconciliationTool/BankReconciliationTool.exe`

### Create Windows Installer
1. Build executable first (above)
2. Open `installer_script.iss` in Inno Setup
3. Update these fields if needed:
   - `MyAppPublisher` - Your company name
   - `MyAppURL` - Your website
4. Click **Build** → **Compile**
5. Installer created: `installers/BankReconciliationTool_Setup_v1.0.0.exe`

### Installer Features
✅ Desktop shortcut
✅ Start menu entry
✅ Uninstaller
✅ Custom installation directory
✅ Professional appearance
✅ Launch on finish option

---

## 🧪 Testing

### Test Executable
```powershell
cd dist\BankReconciliationTool
.\BankReconciliationTool.exe
```

### Test Installer
1. Double-click the installer in `installers/` folder
2. Follow installation wizard
3. Launch from desktop shortcut or start menu
4. Test all features
5. Test uninstallation

### Testing Checklist
- [ ] Application launches without errors
- [ ] Icon displays correctly in taskbar
- [ ] All features work (upload, reconcile, export)
- [ ] Files can be processed correctly
- [ ] Export creates Excel with formatting
- [ ] Desktop shortcut works
- [ ] Start menu entry works
- [ ] Uninstaller removes everything

---

## 🔧 Troubleshooting

### Logo Not Showing
1. Ensure `assets/logo.ico` exists
2. Rebuild with: `pyinstaller BankReconciliationTool.spec`
3. Check icon in Windows Explorer → Right-click .exe → Properties

### Build Errors
```powershell
# Clean and rebuild
rmdir /s /q dist build
pip install --upgrade pyinstaller
pyinstaller BankReconciliationTool.spec
```

### Missing Dependencies
```powershell
pip install -r requirements.txt
pip install xlsxwriter openpyxl pillow
```

### Antivirus Flagging
- Add exception in your antivirus
- Sign the executable with a code signing certificate
- Use trusted certificate authorities

---

## 📦 Distribution Checklist

Before distributing:
- [ ] Test on clean Windows machine
- [ ] Verify all features work
- [ ] Check logo displays correctly
- [ ] Update version number in `installer_script.iss`
- [ ] Add license/EULA if needed
- [ ] Create user documentation
- [ ] Test installer on Windows 10 and 11
- [ ] Consider code signing certificate (optional but recommended)

---

## 🆘 Support

### Documentation
- `CREATE_INSTALLER_GUIDE.md` - Detailed installer creation guide
- `assets/README.md` - Logo creation guide
- `README.md` - Application documentation

### Quick Commands
```powershell
# Build everything automatically
.\build.bat

# Just create logo
python create_logo.py

# Just build executable
pyinstaller BankReconciliationTool.spec

# Clean build folders
rmdir /s /q dist build
```

---

## 📝 Version History

### v1.0.0 (Current)
- Initial release
- Bank ledger reconciliation
- Excel export with formatting
- Difference column
- Remarks column
- Full row highlighting
- Auto-filters on headers
