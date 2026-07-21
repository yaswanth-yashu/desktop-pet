🐾 Blobby Pet - Custom Codex-Style Pet
Files Included
plain
my_pet/
├── pet.json              # Pet manifest (Codex-compatible)
├── spritesheet.png       # Sprite atlas (1536x1872, 8x9 grid)
└── spritesheet.webp      # WebP version

my_pet_renderer/
├── index.html            # Standalone browser renderer
└── spritesheet.png       # Copy this from ../my_pet/
How to Use in Codex
Copy the my_pet/ folder to:
Windows: %USERPROFILE%\.codex\pets\blobby\
Mac/Linux: ~/.codex/pets/blobby/
Restart Codex → Settings → Appearance → Pets → Select "Blobby"
How to Run the Standalone Renderer
Copy spritesheet.png from my_pet/ into my_pet_renderer/
Open index.html in any modern browser (Chrome, Firefox, Edge, Safari)
Click buttons to change states, click the pet to interact!
Features:
9 animation states with correct frame counts
Click interaction with particle effects
Speed control slider (1-20 FPS)
Keyboard shortcuts: 1-9 for states, Space to pause
Real-time stats panel showing current state/frame
How to Make Your Own Custom Pet
Option 1: Replace the Sprite Atlas
Open spritesheet.png in any image editor (Photoshop, GIMP, Figma, Aseprite)
Keep the 1536×1872 size and 8×9 grid (192×208 cells)
Draw your character in each cell following the state layout:
Row 0: Idle (6 frames)
Row 1: Running Right (8 frames)
Row 2: Waving (4 frames)
Row 3: Jumping (5 frames)
Row 4: Failed/Error (8 frames)
Row 5: Waiting (6 frames)
Row 6: Running (6 frames)
Row 7: Running Left (8 frames)
Row 8: Review/Thinking (6 frames)
Save as PNG with transparent background
Update pet.json with your pet's name and description
Option 2: Use the Python Generator
Modify the draw_pet() function in the generator script to draw your own character. Change colors, shapes, add accessories, etc. The code handles all the grid layout automatically.
Technical Specs
Table
Property	Value
Atlas Size	1536 × 1872 px
Grid	8 columns × 9 rows
Cell Size	192 × 208 px
Total Frames	72 (57 used)
Format	PNG or WebP with transparency
Frame Rate	~8 FPS (configurable)
State Descriptions
Table
State	Row	Frames	Description
idle	0	6	Gentle breathing/bobbing
runningRight	1	8	Moving right with leg motion
waving	2	4	Arm waving hello
jumping	3	5	Upward arc motion
failed	4	8	Sad/dejected with sweat drops
waiting	5	6	Subtle impatient motion
running	6	6	Forward running
runningLeft	7	8	Moving left (mirror of right)
review	8	6	Thinking with thought bubbles
License
Free to use, modify, and distribute. Have fun! 🎉


my_pet/
├── pet.json              # Pet manifest (Codex-compatible)
├── spritesheet.png       # Sprite atlas (1536x1872, 8x9 grid)
└── spritesheet.webp      # WebP version

my_pet_renderer/
├── index.html            # Standalone browser renderer
└── spritesheet.png       # Copy this from ../my_pet/