# Level 1 Shaman Enhancements

This document outlines the enhancements made to the WoW Classic Bot Agent to better support a Level 1 Shaman character.

## Key Binding Changes

### New Shaman-Specific Keys
- `MELEE_ATTACK_KEY = '1'` - Melee attack (primary for low mana situations)
- `LIGHTNING_BOLT_KEY = '2'` - Lightning bolt spell (ranged attack, costs mana)
- `FACE_TARGET_KEY = 'f'` - Turn to face selected target (if available in your keybinds)
- `STRAFE_LEFT_KEY = 'z'` - Strafe left for dodging
- `STRAFE_RIGHT_KEY = 'c'` - Strafe right for dodging

### Legacy Compatibility
- `ATTACK_SPELL_KEY` now points to `LIGHTNING_BOLT_KEY` for backward compatibility

## New Actions Available

### Combat Actions
- `melee_attack` - Close-range physical attack (no mana cost)
- `lightning_bolt` - Ranged spell attack (costs mana)
- `target_enemy` - Target nearest hostile creature
- `face_target` - Turn to face current target (if available)

### Movement Actions
- `move_forward` / `move_backward` - Basic movement
- `strafe_left` / `strafe_right` - Dodge attacks while maintaining target
- `turn_left` / `turn_right` - Change facing direction
- `flee` - Retreat from combat

### Utility Actions
- `heal` - Use healing potion
- `jump` - Make character jump
- `wait` - Do nothing (safe default)

## Enhanced AI Strategy

The LLM prompt has been updated with shaman-specific combat strategy:

### Combat Priority
1. **Target Selection**: If enemy visible but not targeted → `target_enemy`
2. **Ranged Combat**: If enemy targeted and have mana → `lightning_bolt`
3. **Melee Combat**: If enemy targeted but low/no mana → `melee_attack`
4. **Positioning**: If enemy too far for melee → `move_forward` to get closer
5. **Facing**: If not facing enemy → `face_target` (if available)
6. **Survival**: If health critically low → `heal`
7. **Exploration**: If no enemies → `move_forward`
8. **Retreat**: If overwhelmed → `flee`

### Character Awareness
- Recognizes Level 1 Shaman limitations (limited mana)
- Prioritizes mana conservation by using melee when appropriate
- Uses ranged lightning bolt when mana is available
- Understands positioning requirements for different attack types

## Technical Improvements

### Action Validation
- Updated allowed actions list in `llm_interface.py` to include all new shaman actions
- Enhanced action executor with new methods for each shaman ability
- Improved key binding organization in `config.py`

### Key Conflict Resolution
- Moved strafe keys to avoid conflicts with heal potion key
- Clear documentation of key bindings and their purposes

## Usage Notes

### In-Game Setup
Ensure your WoW Classic key bindings match the configuration:
- Slot 1: Melee attack ability
- Slot 2: Lightning Bolt spell
- 'f': Face target (if available in your keybinds)
- 'z': Strafe left
- 'c': Strafe right
- 'q': Healing potion
- 'tab': Target nearest enemy

### Mana Management
The AI will automatically:
- Use lightning bolt when mana is available
- Switch to melee attacks when mana is low
- Move forward to get closer to targets for melee range
- Prioritize survival over aggressive combat

## Testing

The enhanced agent has been tested and successfully:
- Recognizes all new action types
- Executes shaman-specific combat strategies
- Handles movement and targeting appropriately
- Maintains backward compatibility with existing functionality

Run `python3 test_keys.py` to verify key input functionality with the new bindings.