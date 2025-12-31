#!/usr/bin/env python3
"""Simple test script for ImageObjectFinder - shows all contours/components."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from infrastructure_layer.services import ImageObjectFinder


def main():
    """Test ImageObjectFinder with sample images - show all components."""
    finder = ImageObjectFinder()
    
    # Test with images from the 00001 directory
    image_root = project_root / "images" / "00001"
    
    # Test images
    test_images = [
        image_root / "00001_F.jpg",  # Front
        image_root / "00001_T.jpg",  # Top
    ]
    
    print("=" * 70)
    print("Testing ImageObjectFinder - All Components")
    print("=" * 70)
    
    for image_path in test_images:
        if not image_path.exists():
            print(f"\n⚠️  Image not found: {image_path}")
            continue
        
        print(f"\n📸 Processing: {image_path.name}")
        print("-" * 70)
        
        try:
            # Get largest object (main result)
            result = finder.find_object(
                image_path=str(image_path),
                background_is_white=True,
                save_intermediate_results=True,
                output_prefix=image_path.stem.split("_")[-1].lower(),
            )
            
            if result:
                print(f"✅ Largest object found:")
                print(f"   Area: {result.area:.2f} pixels")
                print(f"   Width: {result.width_px:.2f} px")
                print(f"   Height: {result.height_px:.2f} px")
                print(f"   Center: ({result.center_x:.2f}, {result.center_y:.2f})")
            
            # Find ALL contours/components
            print(f"\n🔍 Finding all components...")
            all_results = finder.find_all_objects(
                image_path=str(image_path),
                background_is_white=True,
                save_intermediate_results=False,  # Already saved above
                output_prefix=image_path.stem.split("_")[-1].lower(),
                min_contour_size=10,
            )
            
            print(f"   Total components found: {len(all_results)}")
            print(f"\n   Component details (sorted by area):")
            print(f"   {'#':<4} {'Area':<12} {'Width':<10} {'Height':<10} {'Center X':<10} {'Center Y':<10}")
            print(f"   {'-'*4} {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
            
            for idx, result in enumerate(all_results, start=1):
                print(f"   {idx:<4} {result.area:<12.0f} {result.width_px:<10.2f} {result.height_px:<10.2f} {result.center_x:<10.2f} {result.center_y:<10.2f}")
            
            # Check intermediate files
            intermediate_dir = image_path.parent / "_intermediate"
            if intermediate_dir.exists():
                intermediate_files = list(intermediate_dir.glob(f"{image_path.stem}_intermediate_*"))
                print(f"\n   Intermediate files saved: {len(intermediate_files)}")
                for f in sorted(intermediate_files)[:5]:  # Show first 5
                    print(f"      - {f.name}")
                if len(intermediate_files) > 5:
                    print(f"      ... and {len(intermediate_files) - 5} more")
                
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

