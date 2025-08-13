#!/usr/bin/env python3
"""Simple launcher script for the WoW Classic Bot Agent."""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_dependencies():
    """Quick check for essential dependencies."""
    try:
        import ollama
        import pyautogui
        import mss
        from PIL import Image
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


def check_ollama_service():
    """Quick check if Ollama is accessible."""
    try:
        import ollama
        client = ollama.Client()
        client.list()
        return True
    except Exception:
        print("❌ Cannot connect to Ollama service.")
        print("Please ensure Ollama is running: ollama serve")
        return False


def main():
    """Main launcher function."""
    print("🎮 WoW Classic Bot Agent Launcher")
    print("=" * 35)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Quick pre-flight checks
    print("Running pre-flight checks...")
    
    if not check_dependencies():
        print("\n💡 Run setup first: python setup.py")
        return 1
    
    if not check_ollama_service():
        print("\n💡 Start Ollama: ollama serve")
        return 1
    
    print("✅ Pre-flight checks passed!")
    print()
    
    # Launch options
    print("Launch Options:")
    print("1. Run Agent (main.py)")
    print("2. Test Components (test_components.py)")
    print("3. Setup/Configuration (setup.py)")
    print("0. Exit")
    
    try:
        choice = input("\nSelect option (0-3): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            return 0
        elif choice == '1':
            print("\n🚀 Launching WoW Classic Bot Agent...")
            print("Press Ctrl+C to stop the agent.")
            print("-" * 40)
            return subprocess.call([sys.executable, "main.py"])
        elif choice == '2':
            print("\n🧪 Running Component Tests...")
            return subprocess.call([sys.executable, "test_components.py"])
        elif choice == '3':
            print("\n⚙️  Running Setup...")
            return subprocess.call([sys.executable, "setup.py"])
        else:
            print("Invalid choice. Please select 0-3.")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())