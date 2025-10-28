# Logo and Icon Setup

## Current Status
The `assets` folder has been created to store your logo and icon files.

## What You Need to Add

### 1. Application Icon (logo.ico)
- **File name**: `logo.ico`
- **Location**: `assets/logo.ico`
- **Purpose**: Shows as the application icon in Windows
- **Requirements**: 
  - Format: .ico file
  - Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
  
### 2. Application Logo (logo.png)
- **File name**: `logo.png`
- **Location**: `assets/logo.png`
- **Purpose**: Shows in the application UI
- **Requirements**:
  - Format: .png with transparent background
  - Recommended size: 256x256 or 512x512 pixels

### 3. Installer Banner (Optional)
- **File name**: `installer_banner.bmp`
- **Location**: `assets/installer_banner.bmp`
- **Purpose**: Large image on left side of installer
- **Requirements**:
  - Format: .bmp
  - Size: 164x314 pixels

### 4. Installer Small Icon (Optional)
- **File name**: `installer_small.bmp`
- **Location**: `assets/installer_small.bmp`
- **Purpose**: Small image in installer header
- **Requirements**:
  - Format: .bmp
  - Size: 55x58 pixels

## How to Create/Convert Icons

### Method 1: Online Converter (Easiest)
1. Create your logo as PNG (transparent background recommended)
2. Go to: https://convertio.co/png-ico/
3. Upload your PNG
4. Download the ICO file
5. Save as `assets/logo.ico`

### Method 2: Using ImageMagick
```powershell
# Install ImageMagick first, then:
magick convert logo.png -define icon:auto-resize=256,128,64,48,32,16 assets/logo.ico
```

### Method 3: Using GIMP (Free)
1. Open your logo in GIMP
2. Scale image to 256x256
3. Export As → Select ICO format
4. Check all size options
5. Export

## Design Recommendations

### Logo Design Tips:
- ✅ Simple and recognizable
- ✅ Works well at small sizes (16x16)
- ✅ High contrast
- ✅ Professional appearance
- ✅ Represents banking/finance (calculator, chart, coins, etc.)

### Color Scheme Suggestions:
- **Professional Blue**: #4472C4 (matches current UI)
- **Finance Green**: #2E7D32
- **Trust Navy**: #1A237E
- **Modern Teal**: #00897B

## Quick Logo Ideas

### Bank/Finance Symbols:
- 🏦 Bank building
- 📊 Chart/Graph
- ✓ Checkmark with coin
- 📋 Document with checkmark
- 💰 Money bag
- 🔄 Reconciliation arrows
- ⚖️ Balance scales

### Text-Based Logo:
```
╔═══════════╗
║    BR     ║  (Bank Reconciliation)
║  ✓ ═══ ✓  ║
╚═══════════╝
```

## Where to Get Free Logo Resources

1. **Flaticon** - https://www.flaticon.com/ (free icons)
2. **Icons8** - https://icons8.com/ (free icons)
3. **Canva** - https://www.canva.com/ (free logo maker)
4. **LogoMakr** - https://logomakr.com/ (free online tool)

## After Adding Logo

Once you have your logo file (`logo.ico`), update the PyInstaller spec:

```python
# In BankReconciliationTool.spec, modify the EXE section:
exe = EXE(
    ...
    icon='assets/logo.ico',  # Add this line
    ...
)
```

Then rebuild:
```powershell
pyinstaller BankReconciliationTool.spec
```
