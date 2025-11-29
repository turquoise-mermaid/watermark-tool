#!/usr/bin/env python3
"""
Watermark Tool - Add multi-layer watermarks to protect your designs
Version 2.0 - Fixed transparency, overlap prevention, color options
"""

import os
import sys
import json
import random
from tkinter import Tk, filedialog
from PIL import Image, ImageDraw, ImageFont

try:
    import piexif
except ImportError:
    piexif = None
    print("Warning: piexif not installed. Metadata features will be disabled.")
    print("Install with: pip install piexif --break-system-packages")


def convert_dark_to_white(logo_img):
    """Convert all dark pixels (darker than 50% gray) to white"""
    logo = logo_img.convert('RGBA')
    pixels = logo.load()
    
    for y in range(logo.height):
        for x in range(logo.width):
            r, g, b, a = pixels[x, y]
            
            if a == 0:  # Skip transparent pixels
                continue
            
            brightness = (r + g + b) / 3
            
            if brightness < 128:  # Darker than 50% gray
                pixels[x, y] = (255, 255, 255, a)
    
    return logo


def convert_dark_to_black(logo_img):
    """Convert all light pixels (lighter than 50% gray) to black"""
    logo = logo_img.convert('RGBA')
    pixels = logo.load()
    
    for y in range(logo.height):
        for x in range(logo.width):
            r, g, b, a = pixels[x, y]
            
            if a == 0:  # Skip transparent pixels
                continue
            
            brightness = (r + g + b) / 3
            
            if brightness >= 128:  # Lighter than 50% gray
                pixels[x, y] = (0, 0, 0, a)
    
    return logo


def add_watermark(image_path, output_path, config):
    """Add watermark to image with proper transparency and overlap prevention"""
    
    # Load image
    img = Image.open(image_path)
    
    # Convert to RGBA for transparency support
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create transparent overlay layer
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Load font
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arialbd.ttf",
        ]
        font_path = None
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        font_size = int(min(img.width, img.height) * 0.04)
        
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
            print("  ⚠ Using default font (no system fonts found)")
    except Exception as e:
        font = ImageFont.load_default()
        print(f"  ⚠ Font loading error: {e}")
    
    # Auto-convert (c) or (C) to © symbol
    watermark_text = config['text'].replace('(c)', '©').replace('(C)', '©')
    
    # Calculate text dimensions
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Padding for overlap detection
    padding = int(max(text_width, text_height) * 0.2)
    
    # Overlap detection function
    def rectangles_overlap(box1, box2):
        x1, y1, x2, y2 = box1
        x3, y3, x4, y4 = box2
        return not (x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1)
    
    # Generate positions with overlap prevention
    positions = []
    placed_boxes = []
    overlap_warnings = 0
    
    for i in range(config['count']):
        placed = False
        max_attempts = 50
        
        for attempt in range(max_attempts):
            # Density-weighted random position (more in center)
            x_ratio = random.betavariate(2, 2)
            y_ratio = random.betavariate(2, 2)
            x = int(x_ratio * (img.width - text_width))
            y = int(y_ratio * (img.height - text_height))
            
            candidate_box = (
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            )
            
            # Check for overlaps
            overlaps = False
            for existing_box in placed_boxes:
                if rectangles_overlap(candidate_box, existing_box):
                    overlaps = True
                    break
            
            if not overlaps:
                positions.append((x, y))
                placed_boxes.append(candidate_box)
                placed = True
                break
        
        # If couldn't find clear space, place anyway
        if not placed:
            positions.append((x, y))
            placed_boxes.append(candidate_box)
            overlap_warnings += 1
    
    if overlap_warnings > 0:
        print(f"  ⚠ {overlap_warnings} watermark(s) placed with potential overlap (limited space)")
    
    # Choose colors based on config
    use_white = config['color'] == 'white'
    
    if use_white:
        text_color = (255, 255, 255)
        outline_color_base = (0, 0, 0)
    else:
        text_color = (0, 0, 0)
        outline_color_base = (255, 255, 255)
    
    # Draw text watermarks
    text_alpha = int(255 * config['text_opacity'] / 100)
    
    for pos in positions:
        # Outline (half opacity)
        outline_alpha = text_alpha // 2
        outline_color = outline_color_base + (outline_alpha,)
        
        for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            outline_pos = (pos[0] + offset[0], pos[1] + offset[1])
            draw.text(outline_pos, watermark_text, font=font, fill=outline_color)
        
        # Main text
        main_color = text_color + (text_alpha,)
        draw.text(pos, watermark_text, font=font, fill=main_color)
    
    # Add logo if specified
    if config.get('logo_path') and os.path.exists(config['logo_path']):
        try:
            logo = Image.open(config['logo_path']).convert("RGBA")
            
            # Convert logo color based on choice
            if use_white:
                logo = convert_dark_to_white(logo)
            else:
                logo = convert_dark_to_black(logo)
            
            # Resize logo
            max_logo_width = int(img.width * 0.15)
            if logo.width > max_logo_width:
                ratio = max_logo_width / logo.width
                new_size = (max_logo_width, int(logo.height * ratio))
                logo = logo.resize(new_size, Image.Resampling.LANCZOS)
            
            # Position logo
            logo_position = config.get('logo_position', 'bottom-right')
            padding = int(min(img.width, img.height) * 0.02)
            
            if logo_position == 'bottom-right':
                logo_x = img.width - logo.width - padding
                logo_y = img.height - logo.height - padding
            elif logo_position == 'bottom-left':
                logo_x = padding
                logo_y = img.height - logo.height - padding
            elif logo_position == 'top-right':
                logo_x = img.width - logo.width - padding
                logo_y = padding
            elif logo_position == 'top-left':
                logo_x = padding
                logo_y = padding
            else:
                logo_x = img.width - logo.width - padding
                logo_y = img.height - logo.height - padding
            
            # Apply logo opacity
            logo_alpha = int(255 * config['logo_opacity'] / 100)
            outline_alpha = logo_alpha // 2
            
            # Draw logo outline (4 positions like text)
            for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                offset_x = logo_x + offset[0]
                offset_y = logo_y + offset[1]
                
                logo_outline = Image.new('RGBA', logo.size, (0, 0, 0, 0))
                for y in range(logo.height):
                    for x in range(logo.width):
                        r, g, b, a = logo.getpixel((x, y))
                        if a > 0:
                            new_alpha = int(a * outline_alpha / 255)
                            logo_outline.putpixel((x, y), outline_color_base + (new_alpha,))
                
                overlay.paste(logo_outline, (offset_x, offset_y), logo_outline)
            
            # Draw main logo
            logo_main = Image.new('RGBA', logo.size, (0, 0, 0, 0))
            for y in range(logo.height):
                for x in range(logo.width):
                    r, g, b, a = logo.getpixel((x, y))
                    if a > 0:
                        new_alpha = int(a * logo_alpha / 255)
                        logo_main.putpixel((x, y), text_color + (new_alpha,))
            
            overlay.paste(logo_main, (logo_x, logo_y), logo_main)
            
        except Exception as e:
            print(f"  ⚠ Logo error: {e}")
    
    # Composite overlay onto original image (PROPER TRANSPARENCY!)
    result = Image.alpha_composite(img, overlay)
    
    # Convert back to original mode for saving
    if image_path.lower().endswith(('.jpg', '.jpeg')):
        result = result.convert('RGB')
    
    # Add EXIF metadata if available
    if piexif and config.get('metadata'):
        try:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            exif_dict["0th"][piexif.ImageIFD.Copyright] = config['metadata'].encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)
            result.save(output_path, exif=exif_bytes, quality=95)
        except:
            result.save(output_path, quality=95)
    else:
        result.save(output_path, quality=95)
    
    return True


def select_file(title="Select file", filetypes=None):
    """Open file picker dialog with larger window"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    # Make window larger
    root.geometry("800x600")
    
    if filetypes is None:
        filetypes = [("All files", "*.*")]
    
    filepath = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes
    )
    root.destroy()
    return filepath


def select_directory(title="Select folder"):
    """Open folder picker dialog with larger window and clear instructions"""
    print("\n" + "=" * 60)
    print("FOLDER SELECTION:")
    print("In the dialog that opens:")
    print("  1. Navigate to the folder you want")
    print("  2. Click on the folder name to select it")
    print("  3. Click 'Choose' or 'Select Folder' button")
    print("=" * 60 + "\n")
    
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.geometry("800x600")
    
    folder = filedialog.askdirectory(title=title)
    root.destroy()
    return folder


def save_template(config, filename):
    """Save watermark configuration as template"""
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Template saved: {filename}")


def load_template(filename):
    """Load watermark configuration from template"""
    with open(filename, 'r') as f:
        config = json.load(f)
    print(f"✓ Template loaded: {filename}")
    return config


def export_template(config):
    """Export template for sharing"""
    # Remove file paths for portability
    export_config = config.copy()
    export_config.pop('logo_path', None)
    
    filename = input("\nEnter export filename (e.g., my_watermark.json): ").strip()
    if not filename.endswith('.json'):
        filename += '.json'
    
    with open(filename, 'w') as f:
        json.dump(export_config, f, indent=2)
    
    print(f"✓ Template exported: {filename}")
    print("  (Logo path removed for portability - recipient must set their own)")


def main_menu():
    """Display main menu and get user choice"""
    print("\n" + "=" * 60)
    print("WATERMARK TOOL v2.0")
    print("=" * 60)
    print("\n1. Create new watermark configuration")
    print("2. Load existing template")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    return choice


def configure_watermark():
    """Interactive wizard to configure watermark settings"""
    config = {}
    
    print("\n" + "=" * 60)
    print("WATERMARK CONFIGURATION WIZARD")
    print("=" * 60)
    
    # Watermark color choice
    print("\n--- WATERMARK COLOR ---")
    print("Choose the color for your watermarks (text and logo):")
    print("  • Use WHITE for dark/colorful designs")
    print("  • Use BLACK for light/white backgrounds")
    print("\nTip: If your logo has colors, save it as black or white first")
    print("     The tool will convert dark pixels to your chosen color")
    
    while True:
        color_choice = input("\nChoose watermark color (white/black): ").strip().lower()
        if color_choice in ['white', 'black']:
            config['color'] = color_choice
            break
        print("  ⚠ Please enter 'white' or 'black'")
    
    # Logo (optional)
    print("\n--- LOGO (OPTIONAL) ---")
    add_logo = input("Add logo? (y/n): ").strip().lower()
    
    if add_logo == 'y':
        print("\nSelect your logo file...")
        logo_path = select_file(
            title="Select Logo (PNG recommended)",
            filetypes=[("All files", "*.*"), ("PNG files", "*.png"), ("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if logo_path:
            config['logo_path'] = logo_path
            print(f"✓ Logo selected: {os.path.basename(logo_path)}")
            
            # Logo position
            print("\nLogo position:")
            print("  1. Bottom-right (default)")
            print("  2. Bottom-left")
            print("  3. Top-right")
            print("  4. Top-left")
            
            pos_choice = input("\nChoose position (1-4, default=1): ").strip()
            positions = {
                '1': 'bottom-right',
                '2': 'bottom-left',
                '3': 'top-right',
                '4': 'top-left',
                '': 'bottom-right'
            }
            config['logo_position'] = positions.get(pos_choice, 'bottom-right')
            
            # Logo opacity
            while True:
                try:
                    logo_opacity = input("\nLogo opacity % (10-100, default=35): ").strip()
                    if logo_opacity == '':
                        config['logo_opacity'] = 35
                        break
                    logo_opacity = int(logo_opacity)
                    if 10 <= logo_opacity <= 100:
                        config['logo_opacity'] = logo_opacity
                        break
                    print("  ⚠ Opacity must be between 10 and 100")
                except ValueError:
                    print("  ⚠ Please enter a number")
        else:
            print("  ⚠ No logo selected")
    
    # Watermark text
    print("\n--- WATERMARK TEXT ---")
    print("Tip: Type (c) and it will auto-convert to © symbol")
    
    while True:
        text = input("\nEnter watermark text: ").strip()
        if text:
            config['text'] = text
            break
        print("  ⚠ Text cannot be empty")
    
    # Number of watermarks
    while True:
        try:
            count = input("\nNumber of scattered watermarks (default=7): ").strip()
            if count == '':
                config['count'] = 7
                break
            count = int(count)
            if count > 0:
                config['count'] = count
                break
            print("  ⚠ Count must be greater than 0")
        except ValueError:
            print("  ⚠ Please enter a number")
    
    # Text opacity
    while True:
        try:
            text_opacity = input("\nText opacity % (10-100, default=20): ").strip()
            if text_opacity == '':
                config['text_opacity'] = 20
                break
            text_opacity = int(text_opacity)
            if 10 <= text_opacity <= 100:
                config['text_opacity'] = text_opacity
                break
            print("  ⚠ Opacity must be between 10 and 100")
        except ValueError:
            print("  ⚠ Please enter a number")
    
    # Metadata
    add_metadata = input("\nAdd copyright metadata to EXIF? (y/n): ").strip().lower()
    if add_metadata == 'y':
        metadata = input("Enter copyright text (e.g., © 2024 Your Name): ").strip()
        if metadata:
            config['metadata'] = metadata
    
    # Template save disabled in v1.0 (caused crashes in bundled version)
    # Will be re-enabled in v1.1 with proper path handling
    print("\n(Template save feature coming in v1.1)")
    
    return config


def batch_process(config):
    """Process multiple images with watermark"""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING")
    print("=" * 60)
    
    # Select input folder
    print("\nSelect folder containing images to watermark...")
    input_folder = select_directory("Select Input Folder")
    
    if not input_folder:
        print("  ⚠ No folder selected")
        return
    
    # Select output folder
    print("\nSelect folder for watermarked images...")
    output_folder = select_directory("Select Output Folder")
    
    if not output_folder:
        print("  ⚠ No folder selected")
        return
    
    # Find image files
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    image_files = []
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(image_extensions):
            image_files.append(filename)
    
    if not image_files:
        print(f"\n  ⚠ No image files found in {input_folder}")
        return
    
    print(f"\nFound {len(image_files)} image(s) to process")
    print(f"Output folder: {output_folder}\n")
    
    # Process each image
    successful = 0
    failed = 0
    
    for i, filename in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing: {filename}")
        
        input_path = os.path.join(input_folder, filename)
        
        # Generate output filename
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_watermarked{ext}"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            add_watermark(input_path, output_path, config)
            print(f"  ✓ Saved: {output_filename}")
            successful += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"BATCH COMPLETE: {successful} successful, {failed} failed")
    print("=" * 60)


def main():
    """Main program loop"""
    print("\nWelcome to the Watermark Tool!")
    print("Protect your designs from theft with multi-layer watermarks")
    
    while True:
        choice = main_menu()
        
        if choice == '1':
            config = configure_watermark()
            batch_process(config)
        
        elif choice == '2':
            print("\nSelect template file...")
            template_file = select_file(
                title="Select Template",
                filetypes=[("All files", "*.*"), ("JSON files", "*.json")]
            )
            
            if template_file:
                try:
                    config = load_template(template_file)
                    batch_process(config)
                except Exception as e:
                    print(f"  ✗ Error loading template: {e}")
            else:
                print("  ⚠ No template selected")
        
        elif choice == '3':
            print("\nThank you for using Watermark Tool!")
            break
        
        else:
            print("\n  ⚠ Invalid choice. Please enter 1, 2, or 3")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("Please report this issue with the error message above")
