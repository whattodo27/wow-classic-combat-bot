"""Screen capture functionality for the WoW Classic Bot Agent."""

import time
import base64
from io import BytesIO
from typing import Optional, Tuple

import mss
import psutil
from PIL import Image

from config import (
    GAME_WINDOW_TITLE, ALTERNATE_WINDOW_TITLES, SCREENSHOT_DELAY,
    CAPTURE_REGION, IMAGE_QUALITY, MAX_IMAGE_SIZE
)


class ScreenCapture:
    """Handles screen capture operations for the WoW game window."""
    
    def __init__(self):
        self.sct = mss.mss()
        self.game_window_region = None
        self._last_window_check = 0
        self._window_check_interval = 5  # Check for window every 5 seconds
    
    def find_wow_window(self) -> Optional[dict]:
        """Find the World of Warcraft window and return its region."""
        current_time = time.time()
        
        # Only check for window periodically to avoid performance issues
        if current_time - self._last_window_check < self._window_check_interval:
            if self.game_window_region:
                return self.game_window_region
        
        self._last_window_check = current_time
        
        try:
            # On macOS, we need to use different approach
            # For now, we'll capture the primary monitor
            # In a real implementation, you'd use platform-specific window detection
            monitor = self.sct.monitors[1]  # Primary monitor
            self.game_window_region = {
                'top': monitor['top'],
                'left': monitor['left'],
                'width': monitor['width'],
                'height': monitor['height']
            }
            return self.game_window_region
            
        except Exception as e:
            print(f"Error finding WoW window: {e}")
            return None
    
    def capture_game_state(self) -> Optional[str]:
        """Capture the current game state and return as base64 encoded image."""
        try:
            # Find the game window
            window_region = self.find_wow_window()
            if not window_region:
                print("Could not find WoW window")
                return None
            
            # Capture the screen region
            if CAPTURE_REGION:
                # Use custom region if specified
                capture_region = {
                    'top': window_region['top'] + CAPTURE_REGION[1],
                    'left': window_region['left'] + CAPTURE_REGION[0],
                    'width': CAPTURE_REGION[2],
                    'height': CAPTURE_REGION[3]
                }
            else:
                # Use full window
                capture_region = window_region
            
            # Take screenshot
            screenshot = self.sct.grab(capture_region)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Resize if image is too large
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=IMAGE_QUALITY)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Small delay to prevent excessive CPU usage
            time.sleep(SCREENSHOT_DELAY)
            
            return img_base64
            
        except Exception as e:
            print(f"Error capturing game state: {e}")
            return None
    
    def get_window_center(self) -> Optional[Tuple[int, int]]:
        """Get the center coordinates of the game window."""
        if not self.game_window_region:
            self.find_wow_window()
        
        if self.game_window_region:
            center_x = self.game_window_region['left'] + self.game_window_region['width'] // 2
            center_y = self.game_window_region['top'] + self.game_window_region['height'] // 2
            return (center_x, center_y)
        
        return None
    
    def is_wow_running(self) -> bool:
        """Check if World of Warcraft is currently running."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                proc_name = proc.info['name'].lower()
                if 'wow' in proc_name or 'warcraft' in proc_name:
                    return True
            return False
        except Exception:
            return False