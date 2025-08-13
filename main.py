#!/usr/bin/env python3
"""Main WoW Classic Bot Agent - Observe, Think, Act loop."""

import time
import signal
import sys
from typing import Optional

from screen_capture import ScreenCapture
from llm_interface import LLMInterface
from action_executor import ActionExecutor
from config import ACTION_LOOP_DELAY


class WoWClassicAgent:
    """Main agent class that coordinates the observe-think-act loop."""
    
    def __init__(self):
        self.running = False
        self.screen_capture = ScreenCapture()
        self.llm_interface = LLMInterface()
        self.action_executor = ActionExecutor()
        
        # Statistics
        self.cycle_count = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self) -> None:
        """Start the main agent loop."""
        print("Starting WoW Classic Bot Agent...")
        
        # Pre-flight checks
        if not self._run_preflight_checks():
            print("Pre-flight checks failed. Exiting.")
            return
        
        self.running = True
        self.start_time = time.time()
        
        print("Agent started successfully!")
        print("Press Ctrl+C to stop the agent.")
        print("-" * 50)
        
        try:
            while self.running:
                self._run_cycle()
                
                # Print statistics every 10 cycles
                if self.cycle_count % 10 == 0:
                    self._print_statistics()
                
                # Sleep between cycles
                time.sleep(ACTION_LOOP_DELAY)
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received.")
        except Exception as e:
            print(f"\nUnexpected error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the agent and cleanup."""
        if self.running:
            print("\nStopping agent...")
            self.running = False
            
            # Emergency stop to release any held keys
            self.action_executor.emergency_stop()
            
            # Print final statistics
            self._print_final_statistics()
            
            print("Agent stopped successfully.")
    
    def _run_preflight_checks(self) -> bool:
        """Run pre-flight checks before starting the agent."""
        print("Running pre-flight checks...")
        
        # Check if Ollama is running
        print("Checking Ollama connection...")
        if not self.llm_interface.test_connection():
            print("❌ Ollama is not running or not accessible.")
            print("Please start Ollama and ensure the model is available.")
            return False
        print("✅ Ollama connection successful.")
        
        # Check if WoW is running
        print("Checking for World of Warcraft...")
        if not self.screen_capture.is_wow_running():
            print("⚠️  World of Warcraft not detected.")
            print("Please start WoW Classic before running the agent.")
            # Don't fail here, as the process detection might not work perfectly
        else:
            print("✅ World of Warcraft detected.")
        
        # Test screen capture
        print("Testing screen capture...")
        test_image = self.screen_capture.capture_game_state()
        if not test_image:
            print("❌ Screen capture failed.")
            return False
        print("✅ Screen capture successful.")
        
        print("All pre-flight checks passed!")
        return True
    
    def _run_cycle(self) -> None:
        """Run one complete observe-think-act cycle."""
        self.cycle_count += 1
        cycle_start_time = time.time()
        
        print(f"\n--- Cycle {self.cycle_count} ---")
        
        try:
            # OBSERVE: Capture the current game state
            print("📸 Observing game state...")
            image_data = self.screen_capture.capture_game_state()
            
            if not image_data:
                print("❌ Failed to capture game state")
                self.failed_actions += 1
                return
            
            # THINK: Get action from LLM
            print("🤔 Analyzing with LLM...")
            action_plan = self.llm_interface.get_action_from_llm(image_data)
            
            if not action_plan:
                print("❌ Failed to get action from LLM")
                self.failed_actions += 1
                return
            
            # ACT: Execute the planned action
            print("🎮 Executing action...")
            success = self.action_executor.perform_action(action_plan)
            
            if success:
                self.successful_actions += 1
            else:
                self.failed_actions += 1
            
            # Log cycle time
            cycle_time = time.time() - cycle_start_time
            print(f"⏱️  Cycle completed in {cycle_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error in cycle {self.cycle_count}: {e}")
            self.failed_actions += 1
    
    def _print_statistics(self) -> None:
        """Print current agent statistics."""
        if self.start_time:
            runtime = time.time() - self.start_time
            success_rate = (self.successful_actions / max(self.cycle_count, 1)) * 100
            
            print(f"\n📊 Statistics (Runtime: {runtime:.1f}s):")
            print(f"   Cycles: {self.cycle_count}")
            print(f"   Successful actions: {self.successful_actions}")
            print(f"   Failed actions: {self.failed_actions}")
            print(f"   Success rate: {success_rate:.1f}%")
    
    def _print_final_statistics(self) -> None:
        """Print final statistics when stopping."""
        if self.start_time:
            total_runtime = time.time() - self.start_time
            success_rate = (self.successful_actions / max(self.cycle_count, 1)) * 100
            avg_cycle_time = total_runtime / max(self.cycle_count, 1)
            
            print(f"\n📊 Final Statistics:")
            print(f"   Total runtime: {total_runtime:.1f}s")
            print(f"   Total cycles: {self.cycle_count}")
            print(f"   Successful actions: {self.successful_actions}")
            print(f"   Failed actions: {self.failed_actions}")
            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Average cycle time: {avg_cycle_time:.2f}s")


def main():
    """Main entry point."""
    print("WoW Classic Bot Agent v1.0")
    print("=" * 30)
    
    agent = WoWClassicAgent()
    agent.start()


if __name__ == "__main__":
    main()