"""Action execution module for the WoW Classic Bot Agent."""

import time
import subprocess
from typing import Dict, Any, Optional

try:
    import pynput
    from pynput.keyboard import Key, Listener
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    
import pyautogui

from config import (
    HEAL_POTION_KEY, MELEE_ATTACK_KEY, LIGHTNING_BOLT_KEY, MOVE_FORWARD_KEY, MOVE_BACKWARD_KEY,
    TURN_LEFT_KEY, TURN_RIGHT_KEY, JUMP_KEY, TARGET_NEAREST_ENEMY_KEY,
    FACE_TARGET_KEY, STRAFE_LEFT_KEY, STRAFE_RIGHT_KEY,
    ACTION_DELAY, PAUSE_BETWEEN_ACTIONS, FAILSAFE_ENABLED, GAME_WINDOW_TITLE,
    ATTACK_SPELL_KEY  # Legacy compatibility
)


class ActionExecutor:
    """Executes game actions based on LLM decisions."""
    
    def __init__(self):
        # Configure pyautogui settings
        pyautogui.FAILSAFE = FAILSAFE_ENABLED
        pyautogui.PAUSE = PAUSE_BETWEEN_ACTIONS
        
        # Track last focus time to avoid excessive focusing
        self._last_focus_time = 0
        self._focus_interval = 2.0  # Focus window every 2 seconds max
        
        # Initialize keyboard controller if pynput is available
        if PYNPUT_AVAILABLE:
            self.keyboard_controller = keyboard.Controller()
            print("Using pynput for keyboard input (better game compatibility)")
        else:
            self.keyboard_controller = None
            print("Using pyautogui for keyboard input (install pynput for better compatibility)")
        
        # Action mapping
        self.action_map = {
            'attack': self._attack,  # Legacy - uses lightning bolt
            'melee_attack': self._melee_attack,
            'lightning_bolt': self._lightning_bolt,
            'heal': self._heal,
            'move_forward': self._move_forward,
            'move_backward': self._move_backward,
            'turn_left': self._turn_left,
            'turn_right': self._turn_right,
            'strafe_left': self._strafe_left,
            'strafe_right': self._strafe_right,
            'target_enemy': self._target_enemy,
            'face_target': self._face_target,
            'jump': self._jump,
            'wait': self._wait,
            'flee': self._flee
        }
    
    def _focus_wow_window(self) -> bool:
        """Focus the WoW window to ensure it receives keystrokes."""
        current_time = time.time()
        
        # Only focus periodically to avoid performance issues
        if current_time - self._last_focus_time < self._focus_interval:
            return True
            
        try:
            # Simple approach: click on the center of the screen to ensure focus
            # This assumes WoW is visible and covers most of the screen
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            print(f"Clicking at ({center_x}, {center_y}) to focus window")
            pyautogui.click(center_x, center_y)
            time.sleep(0.1)  # Brief pause to ensure focus
            
            self._last_focus_time = current_time
            return True
            
        except Exception as e:
            print(f"Warning: Could not focus WoW window: {e}")
            return False
    
    def perform_action(self, action_data: Dict[str, Any]) -> bool:
        """Execute the action specified by the LLM."""
        try:
            action = action_data.get('action', 'wait')
            reasoning = action_data.get('reasoning', 'No reasoning provided')
            confidence = action_data.get('confidence', 0.5)
            
            print(f"Executing action: {action} (confidence: {confidence:.2f})")
            print(f"Reasoning: {reasoning}")
            
            # Focus WoW window before executing actions (except wait)
            if action != 'wait':
                self._focus_wow_window()
            
            # Execute the action
            if action in self.action_map:
                success = self.action_map[action]()
                if success:
                    print(f"Action '{action}' executed successfully")
                else:
                    print(f"Action '{action}' failed to execute")
                return success
            else:
                print(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"Error executing action: {e}")
            return False
    
    def _send_key(self, key_name: str) -> bool:
        """Send a key using the best available method."""
        try:
            if self.keyboard_controller and PYNPUT_AVAILABLE:
                # Use pynput for better game compatibility
                if key_name == 'tab':
                    self.keyboard_controller.press(Key.tab)
                    self.keyboard_controller.release(Key.tab)
                elif key_name == 'space':
                    self.keyboard_controller.press(Key.space)
                    self.keyboard_controller.release(Key.space)
                else:
                    # For regular characters
                    self.keyboard_controller.press(key_name)
                    self.keyboard_controller.release(key_name)
            else:
                # Fallback to pyautogui
                pyautogui.press(key_name)
            return True
        except Exception as e:
            print(f"Error sending key {key_name}: {e}")
            return False
    
    def _attack(self) -> bool:
        """Execute attack action."""
        try:
            print(f"Sending key: {TARGET_NEAREST_ENEMY_KEY} (target enemy)")
            # First try to target an enemy if not already targeted
            self._send_key(TARGET_NEAREST_ENEMY_KEY)
            time.sleep(ACTION_DELAY)
            
            print(f"Sending key: {ATTACK_SPELL_KEY} (attack)")
            # Then attack
            self._send_key(ATTACK_SPELL_KEY)
            time.sleep(ACTION_DELAY)
            
            return True
        except Exception as e:
            print(f"Error in attack action: {e}")
            return False
    
    def _heal(self) -> bool:
        """Execute heal action."""
        try:
            pyautogui.press(HEAL_POTION_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in heal action: {e}")
            return False
    
    def _move_forward(self) -> bool:
        """Execute move forward action."""
        try:
            pyautogui.keyDown(MOVE_FORWARD_KEY)
            time.sleep(0.5)  # Hold for half a second
            pyautogui.keyUp(MOVE_FORWARD_KEY)
            return True
        except Exception as e:
            print(f"Error in move forward action: {e}")
            return False
    
    def _move_backward(self) -> bool:
        """Execute move backward action."""
        try:
            pyautogui.keyDown(MOVE_BACKWARD_KEY)
            time.sleep(0.5)  # Hold for half a second
            pyautogui.keyUp(MOVE_BACKWARD_KEY)
            return True
        except Exception as e:
            print(f"Error in move backward action: {e}")
            return False
    
    def _turn_left(self) -> bool:
        """Execute turn left action."""
        try:
            pyautogui.keyDown(TURN_LEFT_KEY)
            time.sleep(0.3)  # Hold for a short time
            pyautogui.keyUp(TURN_LEFT_KEY)
            return True
        except Exception as e:
            print(f"Error in turn left action: {e}")
            return False
    
    def _turn_right(self) -> bool:
        """Execute turn right action."""
        try:
            pyautogui.keyDown(TURN_RIGHT_KEY)
            time.sleep(0.3)  # Hold for a short time
            pyautogui.keyUp(TURN_RIGHT_KEY)
            return True
        except Exception as e:
            print(f"Error in turn right action: {e}")
            return False
    
    def _target_enemy(self) -> bool:
        """Execute target enemy action."""
        try:
            pyautogui.press(TARGET_NEAREST_ENEMY_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in target enemy action: {e}")
            return False
    
    def _jump(self) -> bool:
        """Execute jump action."""
        try:
            pyautogui.press(JUMP_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in jump action: {e}")
            return False
    
    def _wait(self) -> bool:
        """Execute wait action (do nothing)."""
        try:
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in wait action: {e}")
            return False
    
    def _flee(self) -> bool:
        """Execute flee action by moving backward and turning."""
        try:
            # Move backward
            pyautogui.keyDown(MOVE_BACKWARD_KEY)
            time.sleep(ACTION_DELAY * 2)  # Hold for longer
            pyautogui.keyUp(MOVE_BACKWARD_KEY)
            
            # Turn around (random direction)
            import random
            turn_key = random.choice([TURN_LEFT_KEY, TURN_RIGHT_KEY])
            pyautogui.keyDown(turn_key)
            time.sleep(ACTION_DELAY)
            pyautogui.keyUp(turn_key)
            
            return True
        except Exception as e:
            print(f"Error in flee action: {e}")
            return False
    
    def _melee_attack(self) -> bool:
        """Execute melee attack action (for when low on mana)."""
        try:
            print(f"Sending key: {TARGET_NEAREST_ENEMY_KEY} (target enemy)")
            # First try to target an enemy if not already targeted
            self._send_key(TARGET_NEAREST_ENEMY_KEY)
            time.sleep(ACTION_DELAY)
            
            print(f"Sending key: {MELEE_ATTACK_KEY} (melee attack)")
            # Then melee attack
            self._send_key(MELEE_ATTACK_KEY)
            time.sleep(ACTION_DELAY)
            
            return True
        except Exception as e:
            print(f"Error in melee attack action: {e}")
            return False
    
    def _lightning_bolt(self) -> bool:
        """Execute lightning bolt spell attack."""
        try:
            print(f"Sending key: {TARGET_NEAREST_ENEMY_KEY} (target enemy)")
            # First try to target an enemy if not already targeted
            self._send_key(TARGET_NEAREST_ENEMY_KEY)
            time.sleep(ACTION_DELAY)
            
            print(f"Sending key: {LIGHTNING_BOLT_KEY} (lightning bolt)")
            # Then cast lightning bolt
            self._send_key(LIGHTNING_BOLT_KEY)
            time.sleep(ACTION_DELAY)
            
            return True
        except Exception as e:
            print(f"Error in lightning bolt action: {e}")
            return False
    
    def _strafe_left(self) -> bool:
        """Execute strafe left action."""
        try:
            print(f"Sending key: {STRAFE_LEFT_KEY} (strafe left)")
            self._send_key(STRAFE_LEFT_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in strafe left action: {e}")
            return False
    
    def _strafe_right(self) -> bool:
        """Execute strafe right action."""
        try:
            print(f"Sending key: {STRAFE_RIGHT_KEY} (strafe right)")
            self._send_key(STRAFE_RIGHT_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in strafe right action: {e}")
            return False
    

    
    def _face_target(self) -> bool:
        """Execute face target action."""
        try:
            print(f"Sending key: {FACE_TARGET_KEY} (face target)")
            self._send_key(FACE_TARGET_KEY)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error in face target action: {e}")
            return False
    
    def emergency_stop(self) -> None:
        """Emergency stop - release all keys."""
        try:
            # Release all movement keys
            keys_to_release = [
                MOVE_FORWARD_KEY, MOVE_BACKWARD_KEY,
                TURN_LEFT_KEY, TURN_RIGHT_KEY
            ]
            
            for key in keys_to_release:
                pyautogui.keyUp(key)
            
            print("Emergency stop executed - all keys released")
        except Exception as e:
            print(f"Error in emergency stop: {e}")
    
    def click_at_position(self, x: int, y: int) -> bool:
        """Click at a specific screen position."""
        try:
            pyautogui.click(x, y)
            time.sleep(ACTION_DELAY)
            return True
        except Exception as e:
            print(f"Error clicking at position ({x}, {y}): {e}")
            return False
    
    def get_mouse_position(self) -> tuple:
        """Get current mouse position."""
        return pyautogui.position()