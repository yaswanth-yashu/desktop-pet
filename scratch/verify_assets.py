import os
import json
from PIL import Image

def verify():
    print("=== Asset Verification Script ===")
    
    # 1. Check folder paths
    paths = {
        "pet_json": "assets/eve/pet.json",
        "spritesheet": "assets/eve/spritesheet.webp"
    }
    
    all_ok = True
    for name, path in paths.items():
        if os.path.exists(path):
            print(f"[✓] Found: {path}")
        else:
            print(f"[X] Missing: {path}")
            all_ok = False
            
    if not all_ok:
        print("[!] Slicing check bypassed due to missing files. Please run setup_project.py first.")
        return

    # 2. Check JSON contents
    try:
        with open(paths["pet_json"], "r") as f:
            data = json.load(f)
        print("[✓] Correctly parsed pet.json")
    except Exception as e:
        print(f"[X] Failed to parse pet.json: {e}")
        return

    # 3. Read image and verify slicing grid
    try:
        img = Image.open(paths["spritesheet"])
        print(f"[✓] Loaded spritesheet image. Size: {img.size[0]}x{img.size[1]} px")
        
        # Read frames properties
        sprite_cfg = data.get("sprite", {})
        width = sprite_cfg.get("width", 128)
        height = sprite_cfg.get("height", 128)
        columns = sprite_cfg.get("columns", 12)
        rows = sprite_cfg.get("rows", 9)
        
        expected_w = width * columns
        expected_h = height * rows
        print(f"    Expected Grid: {columns} columns x {rows} rows with frame size {width}x{height}")
        print(f"    Target Slicing Boundaries: Width {expected_w}px, Height {expected_h}px")
        
        if img.size[0] < expected_w or img.size[1] < expected_h:
            print(f"[!] Warning: Spritesheet is smaller ({img.size[0]}x{img.size[1]}) than expected grid ({expected_w}x{expected_h})")
        else:
            print(f"[✓] Spritesheet dimensions are valid for the configured layout grid")
            
        # Test slice one random animation frame from config
        animations = data.get("animations", {})
        if "idle" in animations:
            frames = animations["idle"].get("frames", [])
            if frames:
                r, c = frames[0]
                left = c * width
                top = r * height
                box = (left, top, left + width, top + height)
                cropped = img.crop(box)
                print(f"[✓] Slicing test successful: Cropped frame at row {r}, col {c} (box={box}) -> crop size {cropped.size}")
    except Exception as e:
        print(f"[X] Failed to load/verify spritesheet grid: {e}")

if __name__ == "__main__":
    verify()
