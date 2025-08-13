"""Configuration settings for the WoW Classic Bot Agent."""

# Game window settings
GAME_WINDOW_TITLE = "World of Warcraft"
ALTERNATE_WINDOW_TITLES = ["WoW", "World of Warcraft Classic"]

# Key bindings
HEAL_POTION_KEY = 'q'
MELEE_ATTACK_KEY = '1'          # Melee attack (primary for low mana)
LIGHTNING_BOLT_KEY = '2'        # Lightning bolt spell (ranged)
MOVE_FORWARD_KEY = 'w'
MOVE_BACKWARD_KEY = 's'
TURN_LEFT_KEY = 'a'
TURN_RIGHT_KEY = 'd'
JUMP_KEY = 'space'
TARGET_NEAREST_ENEMY_KEY = 'tab'
# MOVE_TO_TARGET_KEY removed - this ability doesn't exist in WoW Classic
FACE_TARGET_KEY = 'f'           # Face target (if available in your keybinds)
STRAFE_LEFT_KEY = 'z'           # Strafe left (changed from 'q' to avoid heal conflict)
STRAFE_RIGHT_KEY = 'c'          # Strafe right (changed from 'e' to avoid conflicts)

# Legacy key for backward compatibility
ATTACK_SPELL_KEY = LIGHTNING_BOLT_KEY

# Alternative key bindings for testing (uncomment if standard keys don't work)
# TARGET_NEAREST_ENEMY_KEY = 'f1'  # Try F1 if tab doesn't work
# ATTACK_SPELL_KEY = 'f2'          # Try F2 if '1' doesn't work

# Agent behavior settings
ACTION_LOOP_DELAY = 1.5  # seconds between each action cycle
SCREENSHOT_DELAY = 0.1   # delay after taking screenshot
ACTION_DELAY = 0.2       # delay between individual actions

# Ollama settings
OLLAMA_MODEL = "moondream:latest"  # Using the lightweight moondream model for testing
OLLAMA_BASE_URL = "http://localhost:11434"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30

# Screen capture settings
CAPTURE_REGION = None  # None for full window, or (x, y, width, height) for specific region
IMAGE_QUALITY = 60     # JPEG quality for image compression (reduced for faster processing)
MAX_IMAGE_SIZE = (400, 300)  # Resize large images to this size (reduced for faster processing)

# Safety settings
FAILSAFE_ENABLED = True  # Enable pyautogui failsafe (move mouse to corner to stop)
PAUSE_BETWEEN_ACTIONS = 0.1  # Default pause between pyautogui actions