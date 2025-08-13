"""LLM interface for the WoW Classic Bot Agent using Ollama."""

import json
import time
import threading
import signal
from typing import Dict, Optional, Any

import ollama
from ollama import Client

from config import (
    OLLAMA_MODEL, OLLAMA_BASE_URL, MAX_RETRIES, REQUEST_TIMEOUT
)


class LLMInterface:
    """Handles communication with the Ollama LLM for game decision making."""
    
    def __init__(self):
        self.client = Client(host=OLLAMA_BASE_URL)
        self.model = OLLAMA_MODEL
        self._verify_model_availability()
    
    def _verify_model_availability(self) -> bool:
        """Check if the specified model is available in Ollama."""
        try:
            models_response = self.client.list()
            # Handle different response formats
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            elif isinstance(models_response, dict) and 'models' in models_response:
                models_list = models_response['models']
            else:
                models_list = models_response
            
            available_models = []
            for model in models_list:
                if hasattr(model, 'name'):
                    available_models.append(model.name)
                elif isinstance(model, dict) and 'name' in model:
                    available_models.append(model['name'])
                else:
                    # Handle string representation format like "model='qwen2.5vl:latest' ..."
                    model_str = str(model)
                    if "model='" in model_str:
                        # Extract model name from string representation
                        start = model_str.find("model='") + 7
                        end = model_str.find("'", start)
                        if end > start:
                            available_models.append(model_str[start:end])
                    else:
                        available_models.append(model_str)
            
            if self.model not in available_models:
                print(f"Warning: Model '{self.model}' not found. Available models: {available_models}")
                # Try to use a fallback model
                fallback_models = ['qwen2.5vl:latest', 'llava:latest', 'llava:7b', 'qwen2-vl:latest']
                for fallback in fallback_models:
                    if fallback in available_models:
                        print(f"Using fallback model: {fallback}")
                        self.model = fallback
                        return True
                print("No suitable vision model found. Please install qwen2-vl or llava.")
                return False
            return True
            
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False
    
    def _llm_call_with_timeout(self, prompt: str, image_base64: str) -> Optional[Dict[str, Any]]:
        """Make LLM call with timeout using threading."""
        result = [None]
        exception = [None]
        
        def llm_call():
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt,
                            'images': [image_base64]
                        }
                    ],
                    options={
                        'temperature': 0.1,  # Low temperature for consistent decisions
                        'top_p': 0.9,
                        'num_predict': 100,  # Reduced but sufficient for simple JSON
                        'num_ctx': 1024,     # Reduced context size for speed
                        'num_gpu': 1,        # Use GPU acceleration

                    },
                    stream=False
                )
                result[0] = response
            except Exception as e:
                exception[0] = e
        
        # Start the LLM call in a separate thread
        thread = threading.Thread(target=llm_call)
        thread.daemon = True
        thread.start()
        
        # Wait for the thread to complete or timeout
        thread.join(timeout=REQUEST_TIMEOUT)
        
        if thread.is_alive():
            # Thread is still running, meaning it timed out
            print(f"LLM call timed out after {REQUEST_TIMEOUT} seconds")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def get_action_from_llm(self, image_base64: str) -> Optional[Dict[str, Any]]:
        """Send image to LLM and get action decision."""
        prompt = self._create_game_prompt()
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self._llm_call_with_timeout(prompt, image_base64)
                
                if response is None:
                    print(f"LLM call timed out (attempt {attempt + 1})")
                    continue
                
                # Extract the response content
                response_text = response['message']['content'].strip()
                
                # Try to parse JSON response
                action_data = self._parse_llm_response(response_text)
                if action_data:
                    return action_data
                
                print(f"Failed to parse LLM response (attempt {attempt + 1}): {response_text}")
                
            except Exception as e:
                print(f"Error communicating with LLM (attempt {attempt + 1}): {e}")
                
                # Wait before retrying
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
        
        # If all attempts failed, return default action
        print("All LLM attempts failed, returning default action")
        return self._get_default_action()
    
    def _create_game_prompt(self) -> str:
        """Create the prompt for the LLM to analyze the game state."""
        return """
You are an AI agent playing a Level 1 Shaman in World of Warcraft Classic. Analyze the screenshot and choose the best action.

CHARACTER INFO:
- Level 1 Shaman with limited mana
- Lightning Bolt (key 2): Ranged spell attack, costs mana
- Melee Attack (key 1): Close-range attack, no mana cost
- Low health = use healing potion

COMBAT STRATEGY:
1. If enemy is visible but NOT targeted: "target_enemy"
2. If enemy is targeted and you have mana: "lightning_bolt" (ranged)
3. If enemy is targeted but low/no mana: "melee_attack" (close range)
4. If enemy is too far for melee: "move_forward" to get closer
5. If not facing enemy: "face_target" (if available in keybinds)
6. If health is critically low (red): "heal"
7. If no enemies visible: "move_forward" to explore
8. If surrounded or overwhelmed: "flee"

MOVEMENT OPTIONS:
- "move_forward": Explore/approach enemies
- "move_backward": Retreat from danger
- "strafe_left"/"strafe_right": Dodge attacks while maintaining target
- "turn_left"/"turn_right": Change facing direction
- "face_target": Turn to face selected target (if available)

Available Actions:
- "target_enemy": Target nearest hostile creature
- "lightning_bolt": Cast lightning bolt (ranged, costs mana)
- "melee_attack": Melee attack (close range, no mana cost)
- "face_target": Face current target (if available)
- "move_forward": Move forward
- "move_backward": Move backward
- "strafe_left": Strafe left
- "strafe_right": Strafe right
- "turn_left": Turn left
- "turn_right": Turn right
- "heal": Use healing potion
- "flee": Retreat from combat
- "wait": Do nothing

Respond with ONLY this JSON format:
{
    "action": "action_name",
    "reasoning": "what you see and why you chose this action",
    "confidence": 0.8
}

IMPORTANT: Only JSON, no other text.
"""
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response and extract action data."""
        try:
            # Try to find JSON in the response
            response_text = response_text.strip()
            
            # Remove any markdown code blocks
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                response_text = '\n'.join(json_lines)
            
            # Fix incomplete JSON by adding missing closing brace
            if response_text.count('{') > response_text.count('}'):
                response_text += '}'
            
            # Try to parse as JSON
            action_data = json.loads(response_text)
            
            # Filter to only expected fields
            filtered_data = {
                'action': action_data.get('action', 'wait'),
                'reasoning': action_data.get('reasoning', 'No reasoning provided'),
                'confidence': action_data.get('confidence', 0.5)
            }
            
            # Validate action is in allowed list
            allowed_actions = [
                'attack', 'melee_attack', 'lightning_bolt', 'heal', 'move_forward', 'move_backward',
                'turn_left', 'turn_right', 'strafe_left', 'strafe_right', 'target_enemy',
                'face_target', 'jump', 'flee', 'wait'
            ]
 
            if filtered_data['action'] not in allowed_actions:
                print(f"Invalid action: {filtered_data['action']}, defaulting to wait")
                filtered_data['action'] = 'wait'

            return filtered_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return None
    
    def _get_default_action(self) -> Dict[str, Any]:
        """Return a safe default action when LLM fails."""
        return {
            'action': 'wait',
            'reasoning': 'LLM communication failed, waiting for next cycle',
            'health_status': 'unknown',
            'combat_status': 'unknown',
            'confidence': 0.1
        }
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible."""
        try:
            models = self.client.list()
            return True
        except Exception as e:
            print(f"Cannot connect to Ollama: {e}")
            return False