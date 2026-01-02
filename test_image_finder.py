#!/usr/bin/env python3
"""Simple test script for ImageObjectFinder."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from infrastructure_layer.services import ImageObjectFinder


def main():
    """Test ImageObjectFinder with sample images."""
    finder = ImageObjectFinder()
    
    # Test with images from the 00001 directory
    image_root = project_root / "images" / "00001"
    
    # Test images
    test_images = [
        image_root / "00001_T.jpg",  # Top
        image_root / "00001_D.jpg",  # Down
        image_root / "00001_L.jpg",  # Left
        image_root / "00001_R.jpg",  # Right
        image_root / "00001_F.jpg",  # Front
        image_root / "00001_B.jpg",  # Back
    ]
    
    for image_path in test_images:
        if not image_path.exists():
            continue
        
        intermediate_dir = image_path.parent.parent / "_intermediate"
        
        finder.find_object(
            image_path=str(image_path),
            background_is_white=True,
            intermediate_dir=str(intermediate_dir),
        )


if __name__ == "__main__":
    main()

