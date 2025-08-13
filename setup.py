#!/usr/bin/env python3
"""Setup script for the WoW Classic Bot Agent."""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected.")
        print("This project requires Python 3.8 or higher.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible.")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found.")
        return False
    
    try:
        # Install dependencies
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully.")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def check_ollama_installation():
    """Check if Ollama is installed and accessible."""
    print("\nChecking Ollama installation...")
    
    try:
        # Try to run ollama command
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama command not found.")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama is not installed or not in PATH.")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


def check_ollama_service():
    """Check if Ollama service is running."""
    print("\nChecking Ollama service...")
    
    try:
        # Try to list models (this will fail if service isn't running)
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Ollama service is running.")
            return True
        else:
            print("❌ Ollama service is not running.")
            print("Please start Ollama with: ollama serve")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Ollama service check timed out.")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama service: {e}")
        return False


def check_vision_model():
    """Check if a vision-capable model is available."""
    print("\nChecking for vision models...")
    
    try:
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Could not list Ollama models.")
            return False
        
        models = result.stdout.lower()
        vision_models = ['qwen2-vl', 'qwen2.5vl', 'llava', 'bakllava']
        
        found_models = []
        for model in vision_models:
            if model in models:
                found_models.append(model)
        
        if found_models:
            print(f"✅ Vision models found: {', '.join(found_models)}")
            return True
        else:
            print("❌ No vision models found.")
            print("Please install a vision model:")
            print("  ollama pull qwen2-vl:7b")
            print("  or")
            print("  ollama pull llava:7b")
            return False
            
    except Exception as e:
        print(f"❌ Error checking vision models: {e}")
        return False


def create_config_backup():
    """Create a backup of the default config."""
    print("\nCreating configuration backup...")
    
    config_file = Path(__file__).parent / "config.py"
    backup_file = Path(__file__).parent / "config.py.backup"
    
    try:
        if config_file.exists() and not backup_file.exists():
            import shutil
            shutil.copy2(config_file, backup_file)
            print("✅ Configuration backup created.")
        else:
            print("ℹ️  Configuration backup already exists or config not found.")
        return True
    except Exception as e:
        print(f"❌ Error creating config backup: {e}")
        return False


def run_component_test():
    """Run the component test to verify everything works."""
    print("\nRunning component tests...")
    
    test_script = Path(__file__).parent / "test_components.py"
    
    if not test_script.exists():
        print("❌ Test script not found.")
        return False
    
    try:
        print("Running basic component tests...")
        result = subprocess.run([
            sys.executable, str(test_script), "--all"
        ], timeout=60)
        
        if result.returncode == 0:
            print("✅ Component tests completed.")
            return True
        else:
            print("⚠️  Some component tests failed. Check the output above.")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Component tests timed out.")
        return False
    except Exception as e:
        print(f"❌ Error running component tests: {e}")
        return False


def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "=" * 50)
    print("Setup Complete! Next Steps:")
    print("=" * 50)
    print()
    print("1. Start Ollama (if not already running):")
    print("   ollama serve")
    print()
    print("2. Launch World of Warcraft Classic")
    print("   - Log in to your character")
    print("   - Make sure the game window is visible")
    print()
    print("3. Test the components:")
    print("   python test_components.py")
    print()
    print("4. Run the agent:")
    print("   python main.py")
    print()
    print("5. Stop the agent:")
    print("   - Press Ctrl+C")
    print("   - Or move mouse to top-left corner (if failsafe enabled)")
    print()
    print("Configuration:")
    print("- Edit config.py to customize key bindings")
    print("- Adjust ACTION_LOOP_DELAY for different speeds")
    print("- Change OLLAMA_MODEL if using a different model")
    print()
    print("⚠️  Important: This bot is for educational purposes only.")
    print("   Using automation in online games may violate Terms of Service.")
    print("   Use at your own risk and responsibility.")


def main():
    """Main setup function."""
    print("WoW Classic Bot Agent - Setup Script")
    print("=" * 40)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Ollama Installation", check_ollama_installation),
        ("Ollama Service", check_ollama_service),
        ("Vision Models", check_vision_model),
        ("Config Backup", create_config_backup),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Setup Results")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name:20}: {status}")
        if result:
            passed += 1
    
    print(f"\nSetup Status: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 Setup completed successfully!")
        
        # Ask if user wants to run component tests
        try:
            response = input("\nRun component tests now? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                run_component_test()
        except KeyboardInterrupt:
            print("\nSkipping component tests.")
        
        print_next_steps()
    else:
        print("\n⚠️  Setup incomplete. Please resolve the failed checks above.")
        print("\nCommon solutions:")
        print("- Install Ollama from https://ollama.ai")
        print("- Run 'ollama serve' to start the service")
        print("- Install a vision model: 'ollama pull qwen2-vl:7b'")
        print("- Check Python version (requires 3.8+)")


if __name__ == "__main__":
    main()