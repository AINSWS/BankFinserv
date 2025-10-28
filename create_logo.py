"""
Simple Logo Creator for Bank Reconciliation Tool
Creates a basic logo if you don't have one yet.
Requires: pillow (pip install pillow)
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_logo():
    """Create a simple logo with UF initials"""
    
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    bg_color = (68, 114, 196, 255)  # Blue #4472C4
    text_color = (255, 255, 255, 255)  # White
    accent_color = (46, 125, 50, 255)  # Green
    
    # Draw rounded rectangle background
    padding = 20
    draw.rounded_rectangle(
        [padding, padding, size-padding, size-padding],
        radius=30,
        fill=bg_color
    )
    
    # Draw checkmark accent in top right
    check_size = 40
    check_offset = 60
    draw.line(
        [size-check_offset-20, size//4, size-check_offset-10, size//4+10],
        fill=accent_color,
        width=8
    )
    draw.line(
        [size-check_offset-10, size//4+10, size-check_offset+10, size//4-15],
        fill=accent_color,
        width=8
    )
    
    # Add "UF" text
    try:
        # Try to use a system font
        font_size = 100
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "UF"
    # Get text size using textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    text_x = (size - text_width) // 2 - 10
    text_y = (size - text_height) // 2 + 20
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    # Save as PNG
    png_path = 'assets/logo.png'
    img.save(png_path, 'PNG')
    print(f"✅ Created logo: {png_path}")
    
    # Create ICO with multiple sizes
    ico_path = 'assets/logo.ico'
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"✅ Created icon: {ico_path}")
    
    print("\n📊 Logo created successfully!")
    print("   - PNG: For use in application UI")
    print("   - ICO: For Windows executable icon")
    print("\nYou can now build with: pyinstaller BankReconciliationTool.spec")

if __name__ == "__main__":
    # Make sure assets folder exists
    os.makedirs('assets', exist_ok=True)
    
    try:
        create_simple_logo()
    except ImportError:
        print("❌ Error: Pillow library not installed")
        print("Install it with: pip install pillow")
    except Exception as e:
        print(f"❌ Error creating logo: {e}")
        print("\nAlternative: Create your own logo and save as:")
        print("  - assets/logo.png (256x256 PNG)")
        print("  - assets/logo.ico (ICO with multiple sizes)")
