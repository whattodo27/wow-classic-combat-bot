#!/usr/bin/env python3
"""Enhanced test script to verify key sending to WoW with multiple methods."""

import time
import pyautogui

try:
    from pynput import keyboard
    from pynput.keyboard import Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

def test_accessibility_permissions():
    """Test if accessibility permissions are granted on macOS."""
    print("\n=== Testing Accessibility Permissions ===")
    
    if not PYNPUT_AVAILABLE:
        print("❌ pynput not available - install with: pip3 install pynput")
        return False
        
    try:
        # Try to create a keyboard controller
        kb = keyboard.Controller()
        print("✅ pynput keyboard controller created successfully")
        
        # Try a simple key press test
        print("Testing key press capability...")
        kb.press('f12')  # F12 is usually safe to test
        kb.release('f12')
        print("✅ Key press test successful")
        return True
        
    except Exception as e:
        print(f"❌ Accessibility permission error: {e}")
        print("\n🔧 To fix this on macOS:")
        print("1. Go to System Preferences > Security & Privacy > Privacy")
        print("2. Select 'Accessibility' from the left panel")
        print("3. Click the lock icon and enter your password")
        print("4. Add Terminal (or your Python IDE) to the list")
        print("5. Restart Terminal/IDE after adding")
        return False

def test_pyautogui_method():
    """Test pyautogui key sending."""
    print("\n=== Testing PyAutoGUI Method ===")
    print("Instructions:")
    print("1. Make sure WoW is running and visible")
    print("2. Click on the WoW window to give it focus")
    print("3. Press Enter here to start the test")
    
    input("Press Enter when WoW has focus...")
    
    print("\nStarting pyautogui test in 3 seconds...")
    time.sleep(3)
    
    print("Sending 'tab' key with pyautogui...")
    pyautogui.press('tab')
    time.sleep(1)
    
    print("Sending '1' key with pyautogui...")
    pyautogui.press('1')
    time.sleep(1)
    
    print("PyAutoGUI test complete!")

def test_pynput_method():
    """Test pynput key sending."""
    if not PYNPUT_AVAILABLE:
        print("\n❌ pynput not available - skipping pynput test")
        return
        
    print("\n=== Testing Pynput Method ===")
    print("Instructions:")
    print("1. Make sure WoW is running and visible")
    print("2. Click on the WoW window to give it focus")
    print("3. Press Enter here to start the test")
    
    input("Press Enter when WoW has focus...")
    
    print("\nStarting pynput test in 3 seconds...")
    time.sleep(3)
    
    try:
        kb = keyboard.Controller()
        
        print("Sending 'tab' key with pynput...")
        kb.press(Key.tab)
        kb.release(Key.tab)
        time.sleep(1)
        
        print("Sending '1' key with pynput...")
        kb.press('1')
        kb.release('1')
        time.sleep(1)
        
        print("Pynput test complete!")
        
    except Exception as e:
        print(f"❌ Pynput test failed: {e}")

def main():
    """Main test function."""
    print("🎮 WoW Key Input Test Suite")
    print("===========================\n")
    
    # Test accessibility permissions first
    if not test_accessibility_permissions():
        print("\n⚠️  Accessibility permissions not granted. Some tests may fail.")
    
    while True:
        print("\n📋 Test Options:")
        print("1. Test PyAutoGUI method")
        print("2. Test Pynput method (recommended for games)")
        print("3. Test both methods")
        print("4. Check accessibility permissions")
        print("0. Exit")
        
        choice = input("\nSelect option (0-4): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            test_pyautogui_method()
        elif choice == '2':
            test_pynput_method()
        elif choice == '3':
            test_pyautogui_method()
            test_pynput_method()
        elif choice == '4':
            test_accessibility_permissions()
        else:
            print("Invalid choice. Please select 0-4.")
        
        print("\n" + "="*50)
        response = input("Did you see any response in WoW? (y/n/skip): ").lower()
        if response == 'y':
            print("✅ Great! The key input is working.")
        elif response == 'n':
            print("❌ Keys not working. Try the other method or check permissions.")
        else:
            print("Test completed.")

if __name__ == "__main__":
    main()