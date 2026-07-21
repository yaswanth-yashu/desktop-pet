import os
import shutil
import json

def setup():
    print("=== EVE Desktop Pet Setup ===")
    
    # 1. Create target directories
    os.makedirs("assets/eve", exist_ok=True)
    os.makedirs("engine", exist_ok=True)
    os.makedirs("ui", exist_ok=True)
    os.makedirs("scratch", exist_ok=True)
    
    # Create empty __init__.py files for modules
    with open("engine/__init__.py", "w") as f:
        pass
    with open("ui/__init__.py", "w") as f:
        pass
        
    print("[✓] Created engine/ and ui/ directories")

    # 2. Move spritesheet.webp if it is in the root
    if os.path.exists("spritesheet.webp"):
        shutil.move("spritesheet.webp", "assets/eve/spritesheet.webp")
        print("[✓] Moved spritesheet.webp to assets/eve/spritesheet.webp")
    elif os.path.exists("assets/eve/spritesheet.webp"):
        print("[✓] spritesheet.webp already in assets/eve/spritesheet.webp")
    else:
        print("[!] spritesheet.webp not found in root or assets/eve/")

    # 3. Create enriched pet.json in assets/eve/
    pet_config = {
        "id": "eve",
        "displayName": "EVE",
        "description": "A movie-faithful EVE robot companion with blue LED eyes, animated in Codex digital pet style.",
        "spritesheetPath": "spritesheet.webp",
        "sprite": {
            "width": 192,
            "height": 208,
            "columns": 8,
            "rows": 9
        },
        "defaultAnimation": "idle",
        "scale": 1.0,
        "behavior": {
            "idle": 0.45,
            "walk": 0.25,
            "wave": 0.10,
            "jump": 0.05,
            "review": 0.10,
            "failed": 0.05
        },
        "animations": {
            "idle": {
                "fps": 6,
                "loop": True,
                "frames": [[0, c] for c in range(6)]
            },
            "run_right": {
                "fps": 8,
                "loop": True,
                "frames": [[1, c] for c in range(8)]
            },
            "run_left": {
                "fps": 8,
                "loop": True,
                "frames": [[2, c] for c in range(8)]
            },
            "wave": {
                "fps": 6,
                "loop": False,
                "frames": [[3, c] for c in range(4)]
            },
            "jump": {
                "fps": 8,
                "loop": False,
                "frames": [[4, c] for c in range(5)]
            },
            "failed": {
                "fps": 8,
                "loop": False,
                "frames": [[5, c] for c in range(8)]
            },
            "waiting": {
                "fps": 6,
                "loop": True,
                "frames": [[6, c] for c in range(6)]
            },
            "running": {
                "fps": 10,
                "loop": True,
                "frames": [[7, c] for c in range(6)]
            },
            "review": {
                "fps": 6,
                "loop": False,
                "frames": [[8, c] for c in range(6)]
            }
        }
    }
    
    with open("assets/eve/pet.json", "w") as f:
        json.dump(pet_config, f, indent=2)
    print("[✓] Created assets/eve/pet.json with animation definitions")
    
    # 4. Clean up original pet.json if in root
    if os.path.exists("pet.json"):
        os.remove("pet.json")
        print("[✓] Removed old pet.json from root")

    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Activate your virtual environment:")
    print("   .\\venv\\Scripts\\activate")
    print("2. Install the required dependencies:")
    print("   pip install -r requirements.txt")
    print("3. Run the setup script to restructure and organize:")
    print("   python setup_project.py")
    print("4. Run the application:")
    print("   python main.py")

if __name__ == "__main__":
    setup()
