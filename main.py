import os
import sys
import json
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor, Qt

from engine.sprite import SpriteLoader
from engine.pet import Pet
from ui.transparent_window import TransparentWindow

class DesktopPetApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Scan for companion plugins in assets/
        self.pets_metadata = {}
        self.scan_assets()
        
        # Load user configurations
        self.settings_path = "settings.json"
        self.current_pet_id = "eve"
        self.scale_factor = 0.8  # Default compact scale for modern displays
        self.always_on_top = True
        self.sound_enabled = True
        self.static_mode = True  # Static animation mode default (stays in place)
        self.load_settings()

        # Core references
        self.pet = None
        self.window = None
        
        # Verify if any pet is found
        if not self.pets_metadata:
            # Create a fallback placeholder for EVE if directory is uninitialized
            self.pets_metadata["eve"] = {
                "name": "EVE (Fallback)",
                "dir": "assets/eve",
                "config_path": "assets/eve/pet.json"
            }
            # Create the path structure in case user skipped setup
            os.makedirs("assets/eve", exist_ok=True)

        # Handle initial load
        if self.current_pet_id not in self.pets_metadata:
            self.current_pet_id = list(self.pets_metadata.keys())[0]

        # Initialize the active pet instance
        self.pet = self.load_pet_instance(self.current_pet_id)
        
        # Position pet above taskbar on initial boot
        screen = self.app.primaryScreen().availableGeometry()
        spawn_x = (screen.width() - self.pet.width) // 2
        spawn_y = screen.height() - self.pet.height - 100
        self.pet.physics.x = float(spawn_x)
        self.pet.physics.y = float(spawn_y)

        # Initialize the window layer
        self.window = TransparentWindow(self.pet, self, scale_factor=self.scale_factor)
        
        # Apply window behavior toggles
        if not self.always_on_top:
            self.window.setWindowFlags(self.window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        
        self.window.show()

        # Initialize Gemini Live voice-to-voice client
        from engine.gemini_live import GeminiLiveClient
        self.gemini_client = GeminiLiveClient(self.pet, self)

        # Start game loop timer (60 FPS)
        self.last_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)  # ~60 FPS

    def scan_assets(self):
        """Scans assets/ subdirectories for plugin pets containing pet.json."""
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)
            return

        for entry in os.scandir(assets_dir):
            if entry.is_dir():
                config_file = os.path.join(entry.path, "pet.json")
                if os.path.exists(config_file):
                    try:
                        with open(config_file, "r") as f:
                            data = json.load(f)
                            pet_id = data.get("id", entry.name)
                            display_name = data.get("displayName", entry.name.upper())
                            self.pets_metadata[pet_id] = {
                                "name": display_name,
                                "dir": entry.path,
                                "config_path": config_file
                            }
                            print(f"[Engine] Registered companion plugin: {display_name} ({pet_id})")
                    except Exception as e:
                        print(f"[!] Error parsing plugin config in {entry.path}: {e}")

    def load_pet_instance(self, pet_id):
        """Loads and returns an instance of the chosen pet."""
        meta = self.pets_metadata[pet_id]
        config_path = meta["config_path"]
        asset_dir = meta["dir"]

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[!] Critical: Cannot load config {config_path}: {e}")
            config = {}

        sheet_name = config.get("spritesheetPath", "spritesheet.webp")
        spritesheet_path = os.path.join(asset_dir, sheet_name)

        sprite_cfg = config.get("sprite", {})
        width = sprite_cfg.get("width", 128)
        height = sprite_cfg.get("height", 128)
        columns = sprite_cfg.get("columns", 12)
        rows = sprite_cfg.get("rows", 9)

        # Slice spritesheet frames
        frames, flipped = SpriteLoader.load_spritesheet(
            spritesheet_path, width, height, columns, rows
        )

        pet_instance = Pet(pet_id, config, frames, flipped, asset_dir)
        pet_instance.main_app = self
        pet_instance.sound_enabled = self.sound_enabled
        pet_instance.physics.is_static = self.static_mode
        
        # Initial bounds update
        screen = self.app.primaryScreen().availableGeometry()
        pet_instance.screen_w = screen.width()
        pet_instance.screen_h = screen.height()

        return pet_instance

    def switch_pet(self, pet_id):
        """Swaps current companion while retaining screen coordinates."""
        if pet_id not in self.pets_metadata:
            return

        old_x = int(self.pet.physics.x)
        old_y = int(self.pet.physics.y)
        
        # Shut down window to reset frames cleanly
        if self.window:
            self.window.close()

        self.current_pet_id = pet_id
        
        # Re-initialize
        self.pet = self.load_pet_instance(pet_id)
        if hasattr(self, 'gemini_client') and self.gemini_client:
            self.gemini_client.pet = self.pet
        self.pet.physics.x = float(old_x)
        self.pet.physics.y = float(old_y)

        # Read window flags state
        self.window = TransparentWindow(self.pet, self, scale_factor=self.scale_factor)
        
        if not self.always_on_top:
            self.window.setWindowFlags(self.window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

        self.window.show()
        self.save_settings()
        self.pet.say(f"Switched to {self.pet.config.get('displayName', 'Companion')}!", duration=2.5)

    def get_available_pets(self):
        """Returns a list of tuples containing loaded pet ids and display names."""
        return [(pid, meta["name"]) for pid, meta in self.pets_metadata.items()]

    def game_loop(self):
        """Standard 60 FPS update cycle."""
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # Cap dt to avoid lag jump issues (e.g. dragging window or suspension)
        dt = min(dt, 0.1)

        if self.pet and self.window:
            # Sync screen geometry boundaries (handles resolution/monitor modifications)
            screen = self.app.primaryScreen().availableGeometry()
            self.pet.screen_w = screen.width()
            self.pet.screen_h = screen.height()

            # 1. Update Pet Core Engine (Physics, Anim, AI Behaviors)
            self.pet.update(dt)

            # 2. Check and look toward global cursor positions when idle
            cursor = QCursor.pos()
            self.pet.interaction.handle_hover(cursor.x(), cursor.y())

            # 3. Align physical window position with coordinates
            # Window top-left is shifted up by bubble offset * scale
            if not self.pet.physics.is_dragging:
                bubble_offset = int(self.window.bubble_offset * self.scale_factor)
                self.window.move(
                    int(self.pet.physics.x), 
                    int(self.pet.physics.y - bubble_offset)
                )

            # 4. Trigger redraw
            self.window.update()

    # --- Persistence Settings ---
    
    def load_settings(self):
        """Loads user preferences from settings.json."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    data = json.load(f)
                    self.current_pet_id = data.get("current_pet_id", "eve")
                    self.scale_factor = data.get("scale", 1.5)
                    self.always_on_top = data.get("always_on_top", True)
                    self.sound_enabled = data.get("sound_enabled", True)
                    self.static_mode = data.get("static_mode", True)
            except Exception as e:
                print(f"[!] Warning: Cannot read settings.json: {e}")

    def save_settings(self):
        """Saves user preferences to settings.json."""
        # Read from window layers if loaded
        if self.window:
            self.scale_factor = self.window.scale_factor
            self.always_on_top = bool(self.window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        if self.pet:
            self.sound_enabled = self.pet.sound_enabled

        data = {
            "current_pet_id": self.current_pet_id,
            "scale": self.scale_factor,
            "always_on_top": self.always_on_top,
            "sound_enabled": self.sound_enabled,
            "static_mode": self.static_mode
        }
        
        try:
            with open(self.settings_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Cannot save settings.json: {e}")

    def set_static_mode(self, static_mode):
        """Sets the pet's movement mode (static vs wandering)."""
        self.static_mode = static_mode
        if self.pet:
            self.pet.physics.is_static = static_mode
            if static_mode:
                self.pet.state_machine.change_state("idle")  # Revert to base state
        self.save_settings()
        
        mode_str = "Static (Cycle with Tab/Keys)" if static_mode else "Wandering"
        if self.pet:
            self.pet.say(f"Mode: {mode_str}", duration=2.5)

    def cycle_animation(self):
        """Cycles to the next animation defined in the pet's config."""
        if not self.pet:
            return
        anim_names = list(self.pet.sprite.animations.keys())
        if not anim_names:
            return

        current_name = self.pet.sprite.current_animation.name if self.pet.sprite.current_animation else ""
        try:
            idx = anim_names.index(current_name)
            next_idx = (idx + 1) % len(anim_names)
        except ValueError:
            next_idx = 0

        next_name = anim_names[next_idx]
        self.set_active_animation(next_name)

    def switch_animation_by_index(self, index):
        """Switches to the animation by index order (0-8 keys correspond to 1-9 keyboard inputs)."""
        if not self.pet:
            return
        anim_names = list(self.pet.sprite.animations.keys())
        if 0 <= index < len(anim_names):
            self.set_active_animation(anim_names[index])

    def set_active_animation(self, anim_name):
        """Sets the active animation dynamically."""
        is_voice_chat_active = hasattr(self, 'gemini_client') and self.gemini_client and self.gemini_client.is_active

        if self.static_mode:
            self.pet.sprite.play(anim_name)
            if not is_voice_chat_active:
                self.pet.say(f"Animation: {anim_name}", duration=2.0)
            self.pet.play_sound("click")
        else:
            state_mapping = {
                "idle": "idle",
                "run_left": "walk_left",
                "runningLeft": "walk_left",
                "run_right": "walk_right",
                "runningRight": "walk_right",
                "wave": "wave",
                "waving": "wave",
                "jump": "jump",
                "jumping": "jump",
                "failed": "failed",
                "waiting": "waiting",
                "review": "review"
            }
            state_name = state_mapping.get(anim_name, "idle")
            self.pet.state_machine.change_state(state_name)
            if not is_voice_chat_active:
                self.pet.say(f"State: {state_name}", duration=2.0)

    def exit_application(self):
        """Saves settings and shuts down the pet engine."""
        self.save_settings()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = DesktopPetApp()
    app.run()