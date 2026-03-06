# Top-Down Racing Game

A fun top-down racing game where you race miniature cars around everyday environments!

## Latest Updates (v1.1)

**Bug Fixes:**
- ✅ Fixed AI cars getting stuck on obstacles - now they can reverse and escape
- ✅ Added screen boundaries to prevent cars from driving off the playfield
- ✅ **Proper lap counting system** - must pass all checkpoints AND cross start/finish line
- ✅ Added visible checkered start/finish line on each track
- ✅ Improved checkpoint detection and visibility
- ✅ Added "Next Checkpoint" indicator to HUD for better navigation

**How Lap Counting Works:**
1. Pass through all checkpoints in order (highlighted in yellow)
2. After the last checkpoint, you'll see "Cross FINISH LINE!" message
3. Drive over the checkered start/finish line to complete the lap
4. You cannot skip ahead by crossing the finish line early - checkpoints must be completed first!

## Features

### 🏁 Three Unique Tracks
1. **Desk Circuit** - Race around a cluttered office desk, dodging coffee mugs, keyboards, mice, notepads, and office supplies. **Track edges marked with silver paper clips** showing the racing line.
2. **Living Room** - Navigate through a living room full of furniture including couches, tables, chairs, plants, and a TV stand. **Colorful socks mark the track boundaries** to guide your way.
3. **Garden Circuit** - Speed through a garden with a pond, shed, patio, garden furniture, plant pots, BBQ grill, and a **jump ramp off the steps!** **Beautiful flowers line the track edges** showing where to drive.

### 🏆 Championship Mode
- Race **all three tracks** in sequence
- Cumulative points across all races
- Final **league table** showing your performance on each track
- **Trophy award** for the champion!
- Performance ratings based on total points

### 🏎️ Gameplay
- **3-lap races** against 3 AI opponents
- **Checkpoint system** to prevent cheating and guide the racing line
- **Physics-based car handling** with acceleration, friction, and collision detection
- **BOOST system** - 2 boosts per lap for strategic overtaking
- **Jump mechanics** - hit the garden steps at speed to launch into the air!
- **AI opponents** with pathfinding that navigate the track and avoid obstacles
- **Points system**: Earn points for all finishes
  - 1st place: 25 points
  - 2nd place: 18 points
  - 3rd place: 15 points
  - 4th place: 12 points

### 🎮 Controls
- **Arrow Keys**: Drive your car
  - UP: Accelerate
  - DOWN: Brake/Reverse
  - LEFT/RIGHT: Steer (only works when moving)
- **SPACE (in race)**: Activate BOOST for a burst of speed
  - Get 2 boosts per lap (refills each new lap)
  - Perfect for overtaking opponents!
  - Boost lasts 1 second with 1.8x speed multiplier
- **SPACE (in menu)**: Start race or continue after race
- **LEFT/RIGHT**: Switch tracks in single race mode
- **C**: Toggle between Single Race and Championship Mode

## Installation

1. **Install Python** (3.7 or higher)
   - Download from [python.org](https://www.python.org/downloads/)

2. **Install Pygame**
   ```bash
   pip install pygame
   ```

3. **Run the game**
   ```bash
   python racing_game.py
   ```

## How to Play

### Understanding the HUD
The HUD (top left corner) shows:
- **Lap**: Current lap out of 3
- **Next CP**: Which checkpoint to head for next (highlighted in yellow on track)
  - Changes to **"Cross FINISH LINE!"** when all checkpoints are passed
- **Position**: Your current race position
- **Boost**: Number of boosts remaining (refills each lap)
- **Points**: Your total championship points

### The Checkered Start/Finish Line
- Black and white checkered line visible on each track
- You must cross this line AFTER passing all checkpoints to complete a lap
- Prevents cutting corners and ensures fair racing

### Single Race Mode
1. Launch the game - you'll see the main menu
2. Use LEFT/RIGHT arrows to select a track
3. Press SPACE to start racing
4. Navigate through the checkpoints (shown as circles on the track)
5. Complete 3 laps before your opponents
6. Earn points for your finishing position
7. Return to menu and try another track!

### Championship Mode
1. Press **C** in the menu to enable Championship Mode
2. Press SPACE to start the championship
3. Race all three tracks in sequence (Desk → Living Room → Garden)
4. Your points accumulate across all races
5. After the final race, view the **Championship Results** with:
   - Full league table showing each race result
   - Total points earned
   - Trophy presentation
   - Performance rating (Champion, Great, or Better Luck!)

## Tips for Success

- **Complete all checkpoints in order** - you must pass each checkpoint before you can finish the lap
- **Cross the checkered line** - after all checkpoints, drive over the start/finish line to complete the lap
- **Follow the track markers** - Paper clips, socks, and flowers show you the racing line and track limits
- **Don't cut corners too aggressively** - you need to pass through all checkpoints in order
- **Plan your racing line** - the optimal path around obstacles isn't always obvious
- **Watch your speed** - you can't turn well at high speeds
- **Use the environment** - some obstacles create natural chicanes and curves
- **Save your boosts strategically** - use them on long straights or to defend position
- **Boost timing** - activate boost when you have a clear path ahead for maximum effect
- **Hit the jump at speed** - in the Garden Circuit, approach the steps with good velocity to catch air!
- **Watch for jumping cars** - cars in mid-air can pass over obstacles
- **AI opponents are competitive** - they'll challenge you for position!
- **In Championship Mode** - consistency matters! Even 2nd and 3rd place finishes add up
- **Boost refills each lap** - don't be afraid to use them, you'll get 2 more next lap!

## Code Structure

The game is built with clean, object-oriented Python:

- **Car class**: Handles both player and AI car physics, controls, race progress, and jump mechanics
- **Track class**: Defines circuits with checkpoints, obstacles, starting positions, and special features
- **Obstacle class**: Includes special `is_jump` flag for ramps
- **Game class**: Manages game state, rendering, race logic, and championship tracking
- **Checkpoint system**: Ensures fair racing and lap counting
- **Collision detection**: Prevents cars from driving through obstacles (unless jumping!)
- **Jump system**: Visual effects with shadows, height tracking, and air time
- **Championship mode**: Tracks multi-race progress and displays league tables

## Customization Ideas

Want to extend the game? Here are some ideas:

1. **Add more tracks**: Create new circuits with different themes (kitchen table, playground, beach, etc.)
2. **More obstacles**: Add moving obstacles or different obstacle types
3. **More jumps**: Add jump ramps to other tracks
4. **Power-ups**: Add boost pads, slow zones, or collectibles
5. **More AI cars**: Increase the field size for more competitive racing
6. **Time trials**: Add a time attack mode with ghost cars
7. **Difficulty levels**: Adjust AI speed and aggression
8. **Visual improvements**: Add car sprites, better textures, particle effects for jumps
9. **Sound effects**: Engine sounds, collision sounds, jump whooshes, victory music
10. **Expanded championship**: Add more tracks, longer seasons, or elimination formats
11. **Multiplayer**: Local split-screen or network multiplayer
12. **Weather effects**: Rain that affects grip, wind that affects jumps

## Technical Details

- **Resolution**: 1200x800 pixels
- **FPS**: 60 frames per second
- **Physics**: Simple 2D physics with rotation, acceleration, friction, and jump mechanics
- **AI**: Pathfinding with dynamic obstacle avoidance and jump detection
- **Rendering**: Pygame 2D graphics with geometric shapes and visual effects
- **Game modes**: Single race and championship (3-race series)
- **Tracks**: 3 fully featured circuits with themed obstacles
- **Special features**: Jump ramps with air time and shadow effects

## Requirements

- Python 3.7+
- Pygame 2.0+

Enjoy racing around your desk, living room, and garden! Hit those jumps and become the champion! 🏁🏆
