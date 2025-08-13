#!/usr/bin/env python3
"""Test script for individual components of the WoW Classic Bot Agent."""

import sys
import time
from typing import Optional

from screen_capture import ScreenCapture
from llm_interface import LLMInterface
from action_executor import ActionExecutor


def test_screen_capture() -> bool:
    """Test the screen capture functionality."""
    print("\n=== Testing Screen Capture ===")
    
    try:
        capture = ScreenCapture()
        
        # Test WoW process detection
        print("Checking if WoW is running...")
        wow_running = capture.is_wow_running()
        print(f"WoW detected: {wow_running}")
        
        # Test window finding
        print("Finding WoW window...")
        window = capture.find_wow_window()
        if window:
            print(f"Window found: {window['width']}x{window['height']} at ({window['left']}, {window['top']})")
        else:
            print("No window found")
        
        # Test screenshot capture
        print("Capturing screenshot...")
        image_data = capture.capture_game_state()
        
        if image_data:
            print(f"Screenshot captured successfully (size: {len(image_data)} characters)")
            return True
        else:
            print("Screenshot capture failed")
            return False
            
    except Exception as e:
        print(f"Screen capture test failed: {e}")
        return False


def test_llm_interface() -> bool:
    """Test the LLM interface functionality."""
    print("\n=== Testing LLM Interface ===")
    
    try:
        llm = LLMInterface()
        
        # Test connection
        print("Testing Ollama connection...")
        if not llm.test_connection():
            print("Ollama connection failed")
            return False
        print("Ollama connection successful")
        
        # Test with a simple base64 image (1x1 pixel PNG)
        print("Testing LLM response with dummy image...")
        dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        action_data = llm.get_action_from_llm(dummy_image)
        
        if action_data:
            print(f"LLM response received: {action_data}")
            return True
        else:
            print("LLM response failed")
            return False
            
    except Exception as e:
        print(f"LLM interface test failed: {e}")
        return False


def test_action_executor() -> bool:
    """Test the action executor functionality."""
    print("\n=== Testing Action Executor ===")
    
    try:
        executor = ActionExecutor()
        
        # Test safe actions only
        print("Testing wait action...")
        test_action = {
            'action': 'wait',
            'reasoning': 'Testing action executor',
            'confidence': 1.0
        }
        
        success = executor.perform_action(test_action)
        
        if success:
            print("Action executor test successful")
            return True
        else:
            print("Action executor test failed")
            return False
            
    except Exception as e:
        print(f"Action executor test failed: {e}")
        return False


def test_full_cycle() -> bool:
    """Test a complete observe-think-act cycle."""
    print("\n=== Testing Full Cycle ===")
    
    try:
        # Initialize components
        capture = ScreenCapture()
        llm = LLMInterface()
        executor = ActionExecutor()
        
        print("Running complete cycle...")
        
        # Observe
        print("1. Capturing game state...")
        image_data = capture.capture_game_state()
        if not image_data:
            print("Failed to capture game state")
            return False
        
        # Think
        print("2. Getting action from LLM...")
        action_data = llm.get_action_from_llm(image_data)
        if not action_data:
            print("Failed to get action from LLM")
            return False
        
        # Act (only if it's a safe action)
        print("3. Executing action...")
        if action_data.get('action') in ['wait', 'jump']:  # Only safe actions
            success = executor.perform_action(action_data)
            if not success:
                print("Failed to execute action")
                return False
        else:
            print(f"Skipping potentially unsafe action: {action_data.get('action')}")
        
        print("Full cycle test completed successfully")
        return True
        
    except Exception as e:
        print(f"Full cycle test failed: {e}")
        return False


def interactive_test() -> None:
    """Interactive test mode for manual component testing."""
    print("\n=== Interactive Test Mode ===")
    print("Available tests:")
    print("1. Screen Capture")
    print("2. LLM Interface")
    print("3. Action Executor")
    print("4. Full Cycle")
    print("5. All Tests")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nEnter test number (0-5): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                test_screen_capture()
            elif choice == '2':
                test_llm_interface()
            elif choice == '3':
                test_action_executor()
            elif choice == '4':
                test_full_cycle()
            elif choice == '5':
                run_all_tests()
            else:
                print("Invalid choice. Please enter 0-5.")
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"Error in interactive mode: {e}")


def run_all_tests() -> None:
    """Run all component tests."""
    print("\n" + "=" * 50)
    print("Running All Component Tests")
    print("=" * 50)
    
    tests = [
        ("Screen Capture", test_screen_capture),
        ("LLM Interface", test_llm_interface),
        ("Action Executor", test_action_executor),
        ("Full Cycle", test_full_cycle)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: ❌ FAILED - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agent should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")


def main():
    """Main entry point for the test script."""
    print("WoW Classic Bot Agent - Component Tester")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_all_tests()
        elif sys.argv[1] == "--screen":
            test_screen_capture()
        elif sys.argv[1] == "--llm":
            test_llm_interface()
        elif sys.argv[1] == "--action":
            test_action_executor()
        elif sys.argv[1] == "--cycle":
            test_full_cycle()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --all, --screen, --llm, --action, --cycle")
    else:
        interactive_test()


if __name__ == "__main__":
    main()