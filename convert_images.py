#!/usr/bin/env python
"""
Convert AVIF images to PNG format for better Flutter Web compatibility
"""
import os
from PIL import Image
from pathlib import Path

def convert_avif_to_png(source_dir, output_dir=None):
    """
    Convert all .avif images in source_dir to .png format

    Args:
        source_dir: Directory containing .avif images
        output_dir: Optional output directory (defaults to source_dir)
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir) if output_dir else source_path

    if not source_path.exists():
        print(f"Error: Directory {source_dir} does not exist")
        return

    output_path.mkdir(parents=True, exist_ok=True)

    avif_files = list(source_path.glob("*.avif"))

    if not avif_files:
        print(f"No .avif files found in {source_dir}")
        return

    print(f"Found {len(avif_files)} AVIF files to convert")

    converted = 0
    failed = 0

    for avif_file in avif_files:
        try:
            # Open AVIF image
            img = Image.open(avif_file)

            # Convert to RGB if necessary (AVIF can have alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as PNG (or JPEG if you prefer smaller file sizes)
            output_file = output_path / f"{avif_file.stem}.png"
            img.save(output_file, 'PNG', optimize=True)

            print(f"✓ Converted: {avif_file.name} -> {output_file.name}")
            converted += 1

        except Exception as e:
            print(f"✗ Failed to convert {avif_file.name}: {e}")
            failed += 1

    print(f"\nConversion complete!")
    print(f"Successfully converted: {converted}")
    print(f"Failed: {failed}")

    if converted > 0:
        print(f"\n⚠️  Remember to update your database:")
        print(f"   Update product thumbnails from '.avif' to '.png'")

if __name__ == '__main__':
    # Convert images in static/image/products/
    source_directory = os.path.join(os.path.dirname(__file__), 'static', 'image', 'products')

    print("=" * 60)
    print("AVIF to PNG Converter")
    print("=" * 60)
    print(f"Source directory: {source_directory}\n")

    convert_avif_to_png(source_directory)
