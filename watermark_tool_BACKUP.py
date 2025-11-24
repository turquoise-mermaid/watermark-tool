#!/usr/bin/env python3
"""
Etsy Watermark Protection Tool
Protects your designs from Temu theft with multi-layer watermarking
"""

import os
import sys
import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import piexif

# Try to import tkinter for file dialogs
try:
    from tkinter import Tk, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: tkinter not available. File selection will use manual input.")


class WatermarkTool:
    """Main watermarking tool class"""
    
    def __init__(self):
        self.config_file = "config.json"
        self.config = {"templates": []}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create new"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Validate config structure
                if "templates" not in self.config:
                    self.config["templates"] = []
        except json.JSONDecodeError:
            print("⚠ Template file corrupted. Creating new one.")
            self.config = {"templates": []}
        except Exception as e:
            print(f"⚠ Error loading templates: {e}. Creating new config.")
            self.config = {"templates": []}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving template: {e}")
    
    def get_file_path(self, title="Select a file", filetypes=None):
        """Get file path using tkinter dialog or manual input"""
        if TKINTER_AVAILABLE:
            try:
                root = Tk()
                root.withdraw()  # Hide root window
                root.lift()
                root.attributes('-topmost', True)
                
                if filetypes is None:
                    filetypes = [("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
                
                filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
                root.destroy()
                return filepath if filepath else None
            except Exception as e:
                print(f"⚠ File dialog error: {e}")
                return None
        else:
            # Fallback to manual input
            filepath = input(f"{title}\nEnter file path: ").strip()
            return filepath if filepath and os.path.exists(filepath) else None
    
    def get_directory_path(self, title="Select a folder"):
        """Get directory path using tkinter dialog or manual input"""
        if TKINTER_AVAILABLE:
            try:
                root = Tk()
                root.withdraw()
                root.lift()
                root.attributes('-topmost', True)
                
                dirpath = filedialog.askdirectory(title=title)
                root.destroy()
                return dirpath if dirpath else None
            except Exception as e:
                print(f"⚠ Directory dialog error: {e}")
                return None
        else:
            # Fallback to manual input
            dirpath = input(f"{title}\nEnter directory path: ").strip()
            return dirpath if dirpath and os.path.isdir(dirpath) else None
    
    def validate_logo_file(self, logo_path):
        """Validate logo file meets requirements"""
        if not logo_path or not os.path.exists(logo_path):
            return False, "Logo file not found. Please select a valid file."
        
        # Check file size (50MB limit)
        file_size = os.path.getsize(logo_path) / (1024 * 1024)  # Convert to MB
        if file_size > 50:
            return False, f"Logo file too large ({file_size:.1f}MB). Please use a file smaller than 50MB."
        
        # Check format
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp']
        ext = os.path.splitext(logo_path)[1].lower()
        if ext not in valid_extensions:
            return False, f"Logo must be PNG, JPG, JPEG, or WEBP format. Got: {ext}"
        
        # Try to open the image
        try:
            with Image.open(logo_path) as img:
                img.verify()
            return True, "Valid"
        except Exception as e:
            return False, f"Logo file appears corrupted: {str(e)}"
    
    def setup_wizard(self):
        """Interactive setup wizard for first-time users"""
        print("\n" + "═" * 45)
        print("║  ETSY WATERMARK PROTECTION TOOL           ║")
        print("║  Protect your designs from Temu theft    ║")
        print("═" * 45)
        print("\nWelcome! Let's set up your watermark.")
        print("This will only take 2 minutes.\n")
        input("Press ENTER to continue...")
        
        # Step 1: Logo upload (OPTIONAL)
        print("\n" + "═" * 45)
        print("STEP 1: Your Logo (Optional)")
        print("═" * 45)
        print("\nDo you have a logo to add as a watermark?")
        print("(If not, text-only watermarks work great!)\n")
        print("1. Yes - I have a logo file")
        print("2. No - I'll just use text\n")
        
        logo_path = None
        choice = input("Choose (1 or 2): ").strip()
        
        if choice == "1":
            print("\n✓ Great! A file picker will open.")
            print("Select your logo file (PNG recommended for transparency).")
            input("\nPress ENTER to open file picker...")
            
            logo_path = self.get_file_path(
                title="Select Your Logo",
                filetypes=[("PNG files", "*.png"), ("Image files", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]
            )
            
            if logo_path:
                is_valid, message = self.validate_logo_file(logo_path)
                if is_valid:
                    print(f"\n✓ Logo loaded: {os.path.basename(logo_path)}")
                else:
                    print(f"\n✗ {message}")
                    print("Continuing without logo...")
                    logo_path = None
            else:
                print("\n✗ No logo selected. Continuing without logo...")
        else:
            print("\n✓ No problem! Text watermarks are very effective.")
        
        # Step 2: Text watermark
        print("\n" + "═" * 45)
        print("STEP 2: Text Watermark")
        print("═" * 45)
        print("\nWhat text do you want on your watermark?")
        print("(Example: 'Your Shop Name' or '© 2025 Your Name')\n")
        
        text = input("Enter text: ").strip()
        while not text:
            print("⚠ Text cannot be empty. Please enter your watermark text.")
            text = input("Enter text: ").strip()
        
        print(f"\n✓ Text watermark set: '{text}'")
        
        # Step 3: Watermark count
        print("\n" + "═" * 45)
        print("STEP 3: Watermark Count")
        print("═" * 45)
        print("\nHow many text watermarks should be scattered across the image?")
        print("(More watermarks = harder to remove, but more visible)\n")
        print("Recommended: 7 (good balance)\n")
        
        count_input = input("Enter count (press ENTER for 7): ").strip()
        if count_input and count_input.isdigit():
            count = int(count_input)
            count = max(3, min(count, 20))  # Clamp between 3-20
        else:
            count = 7
        
        print(f"\n✓ Watermark count set: {count}")
        
        # Step 4: Opacity
        print("\n" + "═" * 45)
        print("STEP 4: Watermark Opacity")
        print("═" * 45)
        print("\nHow transparent should the watermark be?")
        print("(Lower opacity = more subtle, higher = more visible)\n")
        print("1. Light (10% opacity - very subtle)")
        print("2. Medium-Light (20% opacity - subtle)")
        print("3. Medium (30% opacity - balanced)")
        print("4. Bold (40% opacity - very visible)\n")
        
        opacity_choice = input("Choose (1, 2, 3, or 4): ").strip()
        opacity_map = {"1": 10, "2": 20, "3": 30, "4": 40}
        opacity = opacity_map.get(opacity_choice, 30)
        
        opacity_label = {10: "Light (10%)", 20: "Medium-Light (20%)", 30: "Medium (30%)", 40: "Bold (40%)"}
        print(f"\n✓ Opacity set: {opacity_label.get(opacity, f'{opacity}%')}")
        
        # Step 5: Logo position (if logo exists)
        logo_position = "bottom-right"  # Default
        if logo_path:
            print("\n" + "═" * 45)
            print("STEP 5: Logo Position")
            print("═" * 45)
            print("\nWhere should your logo be placed?\n")
            print("1. Bottom-right corner (recommended)")
            print("2. Bottom-left corner")
            print("3. Top-right corner")
            print("4. Top-left corner\n")
            
            pos_choice = input("Choose (1, 2, 3, or 4): ").strip()
            pos_map = {"1": "bottom-right", "2": "bottom-left", "3": "top-right", "4": "top-left"}
            logo_position = pos_map.get(pos_choice, "bottom-right")
            
            print(f"\n✓ Logo position: {logo_position}")
        
        # Step 6: Save template
        print("\n" + "═" * 45)
        print(f"STEP {'6' if logo_path else '5'}: Save Your Settings")
        print("═" * 45)
        print("\nPerfect! Let's save this watermark template.")
        print("(You can create multiple templates for different products)\n")
        
        template_name = input("Template name (e.g., 'Sticker Watermark'): ").strip()
        if not template_name:
            template_name = "Default Template"
        
        # Create template object
        template = {
            "name": template_name,
            "logo_path": logo_path,
            "logo_position": logo_position,
            "text": text,
            "count": count,
            "opacity": opacity
        }
        
        # Save template
        self.config["templates"].append(template)
        self.save_config()
        
        print(f"\n✓ Template saved: '{template_name}'")
        print("\n" + "═" * 45)
        print("Setup complete! You can now watermark your images.")
        print("═" * 45)
        input("\nPress ENTER to return to main menu...")
    
    def add_corner_watermark(self, img, logo_path, position, opacity):
        """Add logo to corner of image"""
        try:
            logo = Image.open(logo_path).convert("RGBA")
            
            # Resize logo to 15% of image width (reasonable size)
            max_logo_width = int(img.width * 0.15)
            if logo.width > max_logo_width:
                ratio = max_logo_width / logo.width
                new_size = (max_logo_width, int(logo.height * ratio))
                logo = logo.resize(new_size, Image.Resampling.LANCZOS)
            
            # Apply opacity
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity / 100))
            logo.putalpha(alpha)
            
            # Calculate position with padding
            padding = int(min(img.width, img.height) * 0.02)  # 2% padding
            
            if position == "bottom-right":
                pos = (img.width - logo.width - padding, img.height - logo.height - padding)
            elif position == "bottom-left":
                pos = (padding, img.height - logo.height - padding)
            elif position == "top-right":
                pos = (img.width - logo.width - padding, padding)
            else:  # top-left
                pos = (padding, padding)
            
            # Paste logo
            img.paste(logo, pos, logo)
            
        except Exception as e:
            print(f"⚠ Warning: Could not add logo - {e}")
        
        return img
    
    def add_scattered_watermarks(self, img, text, count, opacity):
        """Add scattered text watermarks using density-weighted placement"""
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Try to use a decent font, fall back to default if not available
        try:
            # Try common font locations
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]
            
            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
            
            # Font size proportional to image size
            font_size = int(min(img.width, img.height) * 0.04)  # 4% of smallest dimension
            
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Generate density-weighted random positions
        # More watermarks in center, fewer at edges
        positions = []
        for _ in range(count):
            # Use beta distribution for density weighting toward center
            x_ratio = random.betavariate(2, 2)  # Peaks at 0.5 (center)
            y_ratio = random.betavariate(2, 2)
            
            x = int(x_ratio * (img.width - text_width))
            y = int(y_ratio * (img.height - text_height))
            
            positions.append((x, y))
        
        # Calculate opacity for text (RGBA format)
        text_opacity = int(255 * opacity / 100)
        
        # Draw all watermarks
        for pos in positions:
            # Semi-transparent text with outline for better visibility
            # Draw outline (slightly darker)
            outline_color = (0, 0, 0, text_opacity // 2)
            for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                outline_pos = (pos[0] + offset[0], pos[1] + offset[1])
                draw.text(outline_pos, text, font=font, fill=outline_color)
            
            # Draw main text (white)
            main_color = (255, 255, 255, text_opacity)
            draw.text(pos, text, font=font, fill=main_color)
        
        return img
    
    def embed_metadata(self, img, template):
        """Embed copyright metadata in image EXIF data"""
        try:
            # Create EXIF data
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            
            # Add copyright info
            copyright_text = f"© {template['text']}"
            exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_text.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Artist] = template['text'].encode('utf-8')
            
            # Convert to bytes
            exif_bytes = piexif.dump(exif_dict)
            
            return exif_bytes
        except Exception as e:
            print(f"⚠ Warning: Could not embed metadata - {e}")
            return None
    
    def apply_watermark(self, input_path, output_path, template):
        """Apply watermark to a single image"""
        try:
            # Open image
            img = Image.open(input_path).convert("RGBA")
            
            # Add logo if exists
            if template.get("logo_path"):
                img = self.add_corner_watermark(
                    img,
                    template["logo_path"],
                    template.get("logo_position", "bottom-right"),
                    template["opacity"]
                )
            
            # Add scattered text watermarks
            img = self.add_scattered_watermarks(
                img,
                template["text"],
                template.get("count", 7),
                template["opacity"]
            )
            
            # Convert back to RGB for saving as JPEG
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format in ['.jpg', '.jpeg']:
                img = img.convert("RGB")
            
            # Prepare metadata
            exif_bytes = self.embed_metadata(img, template)
            
            # Save with metadata
            if exif_bytes and output_format in ['.jpg', '.jpeg']:
                img.save(output_path, exif=exif_bytes, quality=95)
            else:
                img.save(output_path, quality=95)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def watermark_images(self, template):
        """Batch watermark images using template"""
        print("\n" + "═" * 45)
        print("WATERMARK YOUR IMAGES")
        print("═" * 45)
        
        # Select input folder
        print("\nA folder picker will open.")
        print("Select the folder containing images to watermark.")
        input("\nPress ENTER to open folder picker...")
        
        input_folder = self.get_directory_path(title="Select Images Folder")
        
        if not input_folder:
            print("\n✗ No folder selected. Operation cancelled.")
            input("\nPress ENTER to return to main menu...")
            return
        
        # Find images
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        image_files = [
            f for f in os.listdir(input_folder)
            if os.path.splitext(f.lower())[1] in valid_extensions
        ]
        
        if not image_files:
            print(f"\n✗ No images found in selected folder.")
            print(f"   Looking for: PNG, JPG, JPEG, WEBP files")
            input("\nPress ENTER to return to main menu...")
            return
        
        print(f"\n✓ Folder selected: {input_folder}")
        print(f"✓ Found {len(image_files)} images")
        
        # Output location
        print("\nWhere should we save watermarked images?")
        print("1. Same folder (adds '_watermarked' to filenames)")
        print("2. New folder (I'll choose location)\n")
        
        choice = input("Choose (1 or 2): ").strip()
        
        if choice == "2":
            print("\nA folder picker will open.")
            input("Press ENTER to open folder picker...")
            output_folder = self.get_directory_path(title="Select Output Folder")
            if not output_folder:
                print("\n✗ No folder selected. Using same folder as input.")
                output_folder = input_folder
        else:
            output_folder = input_folder
        
        print(f"\n✓ Output folder: {output_folder}")
        
        # Process images
        print("\nProcessing your images...")
        print("(This may take a minute depending on image size and count)\n")
        
        success_count = 0
        failed_files = []
        
        for i, filename in enumerate(image_files, 1):
            input_path = os.path.join(input_folder, filename)
            
            # Create output filename
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_watermarked{ext}"
            output_path = os.path.join(output_folder, output_filename)
            
            # Apply watermark
            success, error = self.apply_watermark(input_path, output_path, template)
            
            if success:
                success_count += 1
            else:
                failed_files.append((filename, error))
            
            # Progress bar
            progress = int((i / len(image_files)) * 20)
            bar = "█" * progress + "░" * (20 - progress)
            percentage = int((i / len(image_files)) * 100)
            print(f"[{i}/{len(image_files)}] {bar} {percentage}%", end='\r')
        
        print("\n")  # New line after progress bar
        
        # Summary
        print("═" * 45)
        if success_count == len(image_files):
            print(f"✓ SUCCESS! All {success_count} images watermarked.")
        else:
            print(f"✓ Completed: {success_count}/{len(image_files)} images watermarked.")
            if failed_files:
                print(f"\n⚠ Failed files ({len(failed_files)}):")
                for fname, error in failed_files[:5]:  # Show first 5
                    print(f"   - {fname}: {error}")
                if len(failed_files) > 5:
                    print(f"   ... and {len(failed_files) - 5} more")
        
        print(f"\nSaved to: {output_folder}")
        print("═" * 45)
        input("\nPress ENTER to return to main menu...")
    
    def export_template(self, template):
        """Export template to JSON file"""
        print("\n" + "═" * 45)
        print("EXPORT TEMPLATE")
        print("═" * 45)
        
        # Get output filename
        default_name = f"{template['name'].replace(' ', '_')}.json"
        print(f"\nExporting template: {template['name']}")
        print(f"Suggested filename: {default_name}\n")
        
        filename = input(f"Enter filename (press ENTER for '{default_name}'): ").strip()
        if not filename:
            filename = default_name
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(template, f, indent=2)
            print(f"\n✓ Template exported: {filename}")
        except Exception as e:
            print(f"\n✗ Export failed: {e}")
        
        input("\nPress ENTER to continue...")
    
    def import_template(self):
        """Import template from JSON file"""
        print("\n" + "═" * 45)
        print("IMPORT TEMPLATE")
        print("═" * 45)
        print("\nSelect a template JSON file to import.")
        input("\nPress ENTER to open file picker...")
        
        filepath = self.get_file_path(
            title="Select Template File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            print("\n✗ No file selected.")
            input("\nPress ENTER to continue...")
            return
        
        try:
            with open(filepath, 'r') as f:
                template = json.load(f)
            
            # Validate template structure
            required_fields = ['name', 'text', 'opacity']
            if not all(field in template for field in required_fields):
                print("\n✗ Invalid template file (missing required fields).")
                input("\nPress ENTER to continue...")
                return
            
            # Check if template with same name exists
            existing_names = [t['name'] for t in self.config['templates']]
            if template['name'] in existing_names:
                template['name'] = f"{template['name']} (imported)"
            
            self.config['templates'].append(template)
            self.save_config()
            
            print(f"\n✓ Template imported: {template['name']}")
        except Exception as e:
            print(f"\n✗ Import failed: {e}")
        
        input("\nPress ENTER to continue...")
    
    def manage_templates(self):
        """Template management menu"""
        while True:
            print("\n" + "═" * 45)
            print("TEMPLATE MANAGEMENT")
            print("═" * 45)
            
            if not self.config['templates']:
                print("\nNo templates found.")
                print("\n1. Create New Template")
                print("2. Import Template")
                print("3. Back to Main Menu\n")
                
                choice = input("Choose option: ").strip()
                
                if choice == "1":
                    self.setup_wizard()
                elif choice == "2":
                    self.import_template()
                elif choice == "3":
                    break
            else:
                print("\nYour templates:\n")
                for i, template in enumerate(self.config['templates'], 1):
                    logo_status = "✓ Logo" if template.get('logo_path') else "Text only"
                    print(f"{i}. {template['name']} ({logo_status}, {template.get('count', 7)} watermarks, {template['opacity']}% opacity)")
                
                print("\n" + "─" * 45)
                print("1. Create New Template")
                print("2. Export Template")
                print("3. Import Template")
                print("4. Delete Template")
                print("5. Back to Main Menu\n")
                
                choice = input("Choose option: ").strip()
                
                if choice == "1":
                    self.setup_wizard()
                elif choice == "2":
                    template_num = input("\nWhich template to export? (number): ").strip()
                    try:
                        idx = int(template_num) - 1
                        if 0 <= idx < len(self.config['templates']):
                            self.export_template(self.config['templates'][idx])
                        else:
                            print("✗ Invalid template number.")
                            input("\nPress ENTER to continue...")
                    except ValueError:
                        print("✗ Invalid input.")
                        input("\nPress ENTER to continue...")
                elif choice == "3":
                    self.import_template()
                elif choice == "4":
                    template_num = input("\nWhich template to delete? (number): ").strip()
                    try:
                        idx = int(template_num) - 1
                        if 0 <= idx < len(self.config['templates']):
                            deleted = self.config['templates'].pop(idx)
                            self.save_config()
                            print(f"\n✓ Deleted template: {deleted['name']}")
                            input("\nPress ENTER to continue...")
                        else:
                            print("✗ Invalid template number.")
                            input("\nPress ENTER to continue...")
                    except ValueError:
                        print("✗ Invalid input.")
                        input("\nPress ENTER to continue...")
                elif choice == "5":
                    break
    
    def main_menu(self):
        """Main menu loop"""
        while True:
            print("\n" + "╔" + "═" * 43 + "╗")
            print("║  ETSY WATERMARK PROTECTION TOOL         ║")
            print("╚" + "═" * 43 + "╝")
            print("\n1. Watermark Images")
            print("2. Manage Templates")
            print("3. Exit\n")
            
            choice = input("Choose option: ").strip()
            
            if choice == "1":
                if not self.config["templates"]:
                    print("\n⚠ No templates found. Let's create one first.\n")
                    input("Press ENTER to continue...")
                    self.setup_wizard()
                else:
                    # Show template selection
                    print("\n" + "═" * 45)
                    print("SELECT TEMPLATE")
                    print("═" * 45)
                    print("\nAvailable templates:\n")
                    
                    for i, t in enumerate(self.config["templates"], 1):
                        logo_status = "✓ Logo" if t.get('logo_path') else "Text only"
                        print(f"{i}. {t['name']} ({logo_status}, {t.get('count', 7)} watermarks)")
                    
                    print()
                    t_choice = input("Choose template (number): ").strip()
                    
                    try:
                        template_idx = int(t_choice) - 1
                        if 0 <= template_idx < len(self.config["templates"]):
                            template = self.config["templates"][template_idx]
                            self.watermark_images(template)
                        else:
                            print("\n✗ Invalid template number.")
                            input("\nPress ENTER to continue...")
                    except ValueError:
                        print("\n✗ Invalid input. Please enter a number.")
                        input("\nPress ENTER to continue...")
            
            elif choice == "2":
                self.manage_templates()
            
            elif choice == "3":
                print("\n" + "═" * 45)
                print("Thank you for using Etsy Watermark Tool!")
                print("Your designs are now protected.")
                print("═" * 45 + "\n")
                sys.exit(0)
            
            else:
                print("\n✗ Invalid option. Please choose 1, 2, or 3.")
                input("\nPress ENTER to continue...")


def main():
    """Main entry point"""
    print("\n")
    print("=" * 45)
    print("  ETSY WATERMARK PROTECTION TOOL v1.0")
    print("  Protect your designs from Temu theft")
    print("=" * 45)
    
    tool = WatermarkTool()
    
    # First time setup if no templates
    if not tool.config["templates"]:
        print("\n👋 First time user detected!")
        print("Let's set up your first watermark template.\n")
        input("Press ENTER to begin setup...")
        tool.setup_wizard()
    
    # Run main menu
    tool.main_menu()


if __name__ == "__main__":
    main()
