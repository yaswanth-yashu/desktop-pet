import os
import sys
import json
import argparse
import numpy as np
from PIL import Image

def convert_spritesheet(input_path, output_dir="assets/custom_pet", src_cols=7, src_rows=13, target_cols=8, target_rows=9, frame_w=192, frame_h=208):
    """
    Automatically detects character contours, trims transparent padding, 
    centers each sprite onto a 192x208 canvas, and creates an EVE-standard 8x9 grid.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)
    out_img_path = os.path.join(output_dir, "spritesheet.webp")
    out_json_path = os.path.join(output_dir, "pet.json")

    src_img = Image.open(input_path).convert("RGBA")
    w, h = src_img.size
    alpha = np.array(src_img)[:, :, 3]

    extracted_sprites = []
    
    # Use connected components to extract distinct character sprites
    try:
        from scipy.ndimage import label, find_objects
        labeled, num_features = label(alpha > 20)
        slices = find_objects(labeled)
        
        boxes = []
        for s in slices:
            ymin, ymax = s[0].start, s[0].stop
            xmin, xmax = s[1].start, s[1].stop
            # Filter out tiny noise pixels
            if (ymax - ymin) > 25 and (xmax - xmin) > 25:
                boxes.append((ymin, ymax, xmin, xmax))
        
        # Sort by row (Y) then column (X)
        boxes.sort(key=lambda b: (b[0] // 80, b[2]))
        for ymin, ymax, xmin, xmax in boxes:
            extracted_sprites.append(src_img.crop((xmin, ymin, xmax, ymax)))
    except Exception:
        pass

    # Fallback to smart grid slicing if contour labeling is unavailable
    if not extracted_sprites:
        src_fw = w / float(src_cols)
        src_fh = h / float(src_rows)
        for r in range(src_rows):
            for c in range(src_cols):
                box = (int(c * src_fw), int(r * src_fh), int((c + 1) * src_fw), int((r + 1) * src_fh))
                cell = src_img.crop(box)
                bbox = cell.getbbox()
                if bbox:
                    extracted_sprites.append(cell.crop(bbox))

    # Build standard 8x9 grid (1536x1872px) with centered 192x208 frames
    new_sheet = Image.new("RGBA", (target_cols * frame_w, target_rows * frame_h), (0, 0, 0, 0))

    num_target_slots = target_cols * target_rows
    for i in range(num_target_slots):
        r_out = i // target_cols
        c_out = i % target_cols
        
        sprite = extracted_sprites[i] if i < len(extracted_sprites) else None
        frame_canvas = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        
        if sprite:
            sw, sh = sprite.size
            max_w, max_h = 160, 175
            scale = min(1.0, max_w / float(sw), max_h / float(sh))
            if scale < 1.0:
                sprite = sprite.resize((int(sw * scale), int(sh * scale)), Image.Resampling.LANCZOS)
                sw, sh = sprite.size
            
            # Place perfectly centered inside frame
            paste_x = (frame_w - sw) // 2
            paste_y = (frame_h - sh) // 2
            frame_canvas.paste(sprite, (paste_x, paste_y), sprite)

        dest_x = c_out * frame_w
        dest_y = r_out * frame_h
        new_sheet.paste(frame_canvas, (dest_x, dest_y))

    new_sheet.save(out_img_path, "WEBP", quality=95)
    print(f"[+] Saved normalized EVE-standard spritesheet: {out_img_path} ({target_cols * frame_w}x{target_rows * frame_h}px)")

    # 4. Generate pet.json matching EVE's structure exactly
    pet_id = os.path.basename(output_dir)
    config = {
        "id": pet_id,
        "displayName": pet_id.replace("_", " ").title(),
        "description": f"Custom companion normalized to EVE standard from {os.path.basename(input_path)}",
        "spritesheetPath": "spritesheet.webp",
        "sprite": {
            "width": frame_w,
            "height": frame_h,
            "columns": target_cols,
            "rows": target_rows
        },
        "defaultAnimation": "idle",
        "scale": 1.0,
        "behavior": {
            "idle": 0.5,
            "walk": 0.3,
            "wave": 0.2
        },
        "animations": {
            "idle": {
                "fps": 6,
                "loop": True,
                "frames": [[0, c] for c in range(target_cols)]
            },
            "run_right": {
                "fps": 8,
                "loop": True,
                "frames": [[1, c] for c in range(target_cols)]
            },
            "run_left": {
                "fps": 8,
                "loop": True,
                "frames": [[2, c] for c in range(target_cols)]
            },
            "wave": {
                "fps": 6,
                "loop": False,
                "frames": [[3, c] for c in range(min(4, target_cols))]
            },
            "jump": {
                "fps": 8,
                "loop": False,
                "frames": [[4, c] for c in range(min(5, target_cols))]
            },
            "failed": {
                "fps": 8,
                "loop": False,
                "frames": [[5, c] for c in range(target_cols)]
            },
            "waiting": {
                "fps": 6,
                "loop": True,
                "frames": [[6, c] for c in range(min(6, target_cols))]
            },
            "review": {
                "fps": 6,
                "loop": False,
                "frames": [[8, c] for c in range(min(6, target_cols))]
            }
        }
    }

    with open(out_json_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[+] Saved pet config: {out_json_path}")
    print(f"[!] New companion registered! Run main.py and select '{pet_id}' in settings.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert any spritesheet image to a normalized EVE-style Desktop Pet companion.")
    parser.add_argument("input_path", help="Path to input image (e.g. astro.webp)")
    parser.add_argument("output_name", nargs="?", default="custom_pet", help="Name of output pet folder (e.g. astrosheet)")
    parser.add_argument("--src_cols", type=int, default=7, help="Number of columns in the source spritesheet (default: 7)")
    parser.add_argument("--src_rows", type=int, default=13, help="Number of rows in the source spritesheet (default: 13)")
    
    args = parser.parse_args()
    out_dir = os.path.join("assets", args.output_name)
    convert_spritesheet(args.input_path, out_dir, src_cols=args.src_cols, src_rows=args.src_rows)
