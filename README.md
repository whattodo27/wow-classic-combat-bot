# WoW Classic Bot Agent

A Python-based AI agent that plays World of Warcraft Classic using computer vision and a local multimodal LLM (Ollama with qwen model). The agent observes the game state through screenshots, analyzes it using AI, and performs actions to play the game autonomously.

## Features

- **Computer Vision**: Captures and analyzes WoW Classic game screenshots
- **AI Decision Making**: Uses Ollama with qwen2-vl model for intelligent gameplay decisions
- **Automated Actions**: Executes mouse clicks and keyboard inputs based on AI analysis
- **Safety Features**: Built-in failsafes and emergency stop functionality
- **Real-time Statistics**: Tracks performance and success rates
- **Configurable**: Easy-to-modify settings for different gameplay styles

## Prerequisites

### System Requirements
- Python 3.8 or higher
- macOS, Windows, or Linux
- World of Warcraft Classic installed and running
- At least 8GB RAM (recommended for LLM operations)

### Ollama Setup
1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull the qwen2-vl model:
   ```bash
   ollama pull qwen2-vl:7b
   ```
   Or alternatively, use llava if qwen2-vl is not available:
   ```bash
   ollama pull llava:7b
   ```
3. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

## Installation

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd MKOAgent
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the agent (optional):
   - Edit `config.py` to customize key bindings and settings
   - Adjust `OLLAMA_MODEL` if using a different model

## Usage

### Quick Start

1. **Start Ollama** (if not already running):
   ```bash
   ollama serve
   ```

2. **Launch World of Warcraft Classic** and log in to your character

3. **Run the agent**:
   ```bash
   python main.py
   ```

4. **Stop the agent** by pressing `Ctrl+C` or moving your mouse to the top-left corner (if failsafe is enabled)

### Configuration

Edit `config.py` to customize the agent behavior:

```python
# Game window settings
GAME_WINDOW_TITLE = "World of Warcraft"

# Key bindings (adjust to match your WoW keybinds)
HEAL_POTION_KEY = 'q'
ATTACK_SPELL_KEY = '1'
MOVE_FORWARD_KEY = 'w'
# ... more settings

# Agent behavior
ACTION_LOOP_DELAY = 1.5  # seconds between actions

# Ollama settings
OLLAMA_MODEL = "qwen2-vl:7b"  # or "llava:7b"
```

## Project Structure

```
MKOAgent/
├── main.py              # Main agent orchestrator
├── config.py            # Configuration settings
├── screen_capture.py    # Screenshot and window detection
├── llm_interface.py     # Ollama/LLM communication
├── action_executor.py   # Game action execution
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## How It Works

The agent follows a continuous **Observe-Think-Act** loop:

1. **Observe**: Captures a screenshot of the WoW game window
2. **Think**: Sends the image to the LLM for analysis and decision-making
3. **Act**: Executes the recommended action (movement, combat, healing, etc.)

### Available Actions

- `attack`: Attack current target or nearest enemy
- `heal`: Use healing potion or spell
- `move_forward/backward`: Character movement
- `turn_left/right`: Character rotation
- `target_enemy`: Target nearest enemy
- `jump`: Make character jump
- `flee`: Run away from danger
- `wait`: Do nothing (safe default)

## Safety Features

- **Failsafe**: Move mouse to top-left corner to emergency stop
- **Emergency Stop**: Releases all held keys when stopping
- **Error Handling**: Graceful handling of LLM and system errors
- **Configurable Delays**: Prevents excessive CPU usage and spam actions

## Troubleshooting

### Common Issues

1. **"Cannot connect to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is installed: `ollama list`
   - Verify the model name in `config.py`

2. **"Could not find WoW window"**
   - Make sure WoW Classic is running and visible
   - Check `GAME_WINDOW_TITLE` in `config.py`
   - Try running as administrator (Windows)

3. **"Screen capture failed"**
   - Check screen permissions (macOS)
   - Ensure WoW is not running in fullscreen exclusive mode
   - Try adjusting `CAPTURE_REGION` in `config.py`

4. **Actions not working in game**
   - Verify key bindings match your WoW settings
   - Make sure WoW window has focus
   - Check if WoW is blocking external input

### Performance Tips

- Use a smaller model like `qwen2-vl:7b` for faster responses
- Increase `ACTION_LOOP_DELAY` to reduce CPU usage
- Adjust `MAX_IMAGE_SIZE` to balance quality vs. speed
- Close unnecessary applications to free up RAM

## Limitations

- **Game Detection**: Window detection may not work perfectly on all systems
- **Model Accuracy**: LLM decisions depend on model quality and prompt engineering
- **Game Updates**: May need adjustments if WoW interface changes
- **Platform Specific**: Some features may work differently across operating systems

## Legal and Ethical Considerations

⚠️ **Important**: This bot is for educational and research purposes only. Using automation tools in online games may violate the game's Terms of Service and could result in account penalties or bans. Use at your own risk and responsibility.

## Contributing

Contributions are welcome! Areas for improvement:
- Better game state detection
- More sophisticated AI prompts
- Additional safety features
- Cross-platform compatibility
- Performance optimizations

## License

This project is provided as-is for educational purposes. Please respect game Terms of Service and use responsibly.