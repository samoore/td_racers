import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (220, 50, 50)
BLUE = (50, 100, 220)
GREEN = (50, 200, 50)
YELLOW = (255, 200, 0)
ORANGE = (255, 140, 0)
BROWN = (139, 69, 19)
WOOD = (205, 133, 63)
LIGHT_BLUE = (173, 216, 230)
DARK_GREEN = (34, 139, 34)
GRASS_GREEN = (124, 252, 0)
WATER_BLUE = (70, 130, 180)
STONE_GRAY = (169, 169, 169)

@dataclass
class Checkpoint:
    x: float
    y: float
    radius: float

@dataclass
class Obstacle:
    x: float
    y: float
    width: float
    height: float
    color: Tuple[int, int, int]
    label: str = ""
    is_jump: bool = False  # Special flag for jump ramps

@dataclass
class TrackMarker:
    """Visual markers that show track edges/limits"""
    x: float
    y: float
    marker_type: str  # "paperclip", "flower", "sock"
    rotation: float = 0  # For variety

@dataclass
class StartFinishLine:
    """The start/finish line where laps are counted"""
    x: float
    y: float
    width: float
    height: float
    angle: float = 0  # Rotation angle

class Car:
    def __init__(self, x, y, color, is_player=False):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.color = color
        self.is_player = is_player
        self.width = 20
        self.height = 30
        self.max_speed = 8 if is_player else 7
        self.acceleration = 0.3
        self.friction = 0.95
        self.turn_speed = 4
        
        # Race stats
        self.lap = 0
        self.checkpoint_index = 0
        self.finished = False
        self.finish_position = None
        self.total_distance = 0
        self.last_checkpoint_passed = -1  # Track which checkpoint was last passed for lap validation
        
        # AI
        self.target_checkpoint = 0
        self.stuck_timer = 0
        self.ai_turn_bias = random.uniform(-0.5, 0.5)
        
        # Jump mechanics
        self.is_jumping = False
        self.jump_timer = 0
        self.jump_height = 0
        
        # Boost mechanics
        self.boost_available = 2  # 2 boosts per lap
        self.is_boosting = False
        self.boost_timer = 0
        self.boost_duration = 60  # 1 second at 60 FPS
        self.boost_multiplier = 1.8
    
    def update_player(self, keys, obstacles):
        # Boost activation
        if keys[pygame.K_SPACE] and self.boost_available > 0 and not self.is_boosting:
            self.is_boosting = True
            self.boost_timer = 0
            self.boost_available -= 1
        
        # Update boost
        if self.is_boosting:
            self.boost_timer += 1
            if self.boost_timer >= self.boost_duration:
                self.is_boosting = False
                self.boost_timer = 0
        
        # Player controls
        boost_factor = self.boost_multiplier if self.is_boosting else 1.0
        
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.acceleration * boost_factor, 
                           self.max_speed * boost_factor)
        elif keys[pygame.K_DOWN]:
            self.speed = max(self.speed - self.acceleration, -self.max_speed * 0.5)
        
        if keys[pygame.K_LEFT]:
            if abs(self.speed) > 0.5:
                self.angle -= self.turn_speed * (abs(self.speed) / self.max_speed)
        if keys[pygame.K_RIGHT]:
            if abs(self.speed) > 0.5:
                self.angle += self.turn_speed * (abs(self.speed) / self.max_speed)
        
        # Apply friction
        self.speed *= self.friction
        
        # Move
        old_x, old_y = self.x, self.y
        rad = math.radians(self.angle)
        self.x += self.speed * math.sin(rad)
        self.y -= self.speed * math.cos(rad)
        
        # Handle jumps
        if self.is_jumping:
            self.jump_timer += 1
            if self.jump_timer < 15:
                self.jump_height = min(self.jump_timer * 2, 20)
            else:
                self.jump_height = max(0, 20 - (self.jump_timer - 15) * 2)
            
            if self.jump_timer >= 30:
                self.is_jumping = False
                self.jump_timer = 0
                self.jump_height = 0
        
        # Keep car within screen boundaries
        margin = 20
        if self.x < margin:
            self.x = margin
            self.speed *= -0.3
        elif self.x > 1200 - margin:  # SCREEN_WIDTH
            self.x = 1200 - margin
            self.speed *= -0.3
        
        if self.y < margin:
            self.y = margin
            self.speed *= -0.3
        elif self.y > 800 - margin:  # SCREEN_HEIGHT
            self.y = 800 - margin
            self.speed *= -0.3
        
        # Collision with obstacles (but not while jumping over them!)
        collision_obs = self.check_collision(obstacles)
        if collision_obs and not self.is_jumping:
            if collision_obs.is_jump and abs(self.speed) > 3:
                # Hit a jump ramp with enough speed!
                self.is_jumping = True
                self.jump_timer = 0
            else:
                self.x, self.y = old_x, old_y
                self.speed *= -0.5
    
    def update_ai(self, checkpoints, obstacles, other_cars):
        if self.finished:
            self.speed *= 0.9
            return
        
        # Get target checkpoint
        target = checkpoints[self.target_checkpoint % len(checkpoints)]
        
        # Calculate angle to target
        dx = target.x - self.x
        dy = target.y - self.y
        target_angle = math.degrees(math.atan2(dx, -dy))
        
        # Calculate angle difference
        angle_diff = target_angle - self.angle
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        # Add some variation to AI driving
        angle_diff += self.ai_turn_bias
        
        # Avoid other cars
        for car in other_cars:
            if car != self:
                dist = math.sqrt((car.x - self.x)**2 + (car.y - self.y)**2)
                if dist < 50:
                    avoid_angle = math.degrees(math.atan2(self.x - car.x, car.y - self.y))
                    avoid_diff = avoid_angle - self.angle
                    angle_diff += avoid_diff * 0.3
        
        # Steering
        if angle_diff > 10:
            self.angle += min(self.turn_speed * 0.8, angle_diff * 0.3)
        elif angle_diff < -10:
            self.angle -= min(self.turn_speed * 0.8, abs(angle_diff) * 0.3)
        
        # Speed control - if stuck, try reversing
        distance_to_target = math.sqrt(dx*dx + dy*dy)
        
        if self.stuck_timer > 20:
            # We're stuck! Reverse and turn
            self.speed = max(self.speed - self.acceleration * 1.5, -self.max_speed * 0.7)
            self.angle += 15 if self.stuck_timer % 2 == 0 else -15
        elif abs(angle_diff) < 30 and distance_to_target > 100:
            self.speed = min(self.speed + self.acceleration * 0.9, self.max_speed)
        else:
            target_speed = self.max_speed * (1 - abs(angle_diff) / 180) * 0.8
            if self.speed < target_speed:
                self.speed += self.acceleration * 0.7
        
        # Apply friction
        self.speed *= self.friction
        
        # Move
        old_x, old_y = self.x, self.y
        rad = math.radians(self.angle)
        self.x += self.speed * math.sin(rad)
        self.y -= self.speed * math.cos(rad)
        
        # Keep AI car within screen boundaries
        margin = 20
        if self.x < margin:
            self.x = margin
            self.speed *= -0.3
            self.angle += 30
        elif self.x > 1200 - margin:  # SCREEN_WIDTH
            self.x = 1200 - margin
            self.speed *= -0.3
            self.angle -= 30
        
        if self.y < margin:
            self.y = margin
            self.speed *= -0.3
            self.angle += 30
        elif self.y > 800 - margin:  # SCREEN_HEIGHT
            self.y = 800 - margin
            self.speed *= -0.3
            self.angle -= 30
        
        # Handle jumps
        if self.is_jumping:
            self.jump_timer += 1
            if self.jump_timer < 15:
                self.jump_height = min(self.jump_timer * 2, 20)
            else:
                self.jump_height = max(0, 20 - (self.jump_timer - 15) * 2)
            
            if self.jump_timer >= 30:
                self.is_jumping = False
                self.jump_timer = 0
                self.jump_height = 0
        
        # Collision with obstacles
        collision_obs = self.check_collision(obstacles)
        if collision_obs and not self.is_jumping:
            if collision_obs.is_jump and abs(self.speed) > 3:
                # Hit a jump ramp with enough speed!
                self.is_jumping = True
                self.jump_timer = 0
            else:
                self.x, self.y = old_x, old_y
                self.speed *= -0.3
                self.angle += random.uniform(-20, 20)
                self.stuck_timer += 1
                
                # If really stuck, try a bigger turn
                if self.stuck_timer > 40:
                    self.angle += 90
                    self.stuck_timer = 0
        else:
            if not collision_obs:
                # Check if we're actually moving
                distance_moved = math.sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
                if distance_moved < 0.5 and abs(self.speed) > 1:
                    # Moving very slowly despite having speed - we're stuck on something
                    self.stuck_timer += 1
                else:
                    self.stuck_timer = max(0, self.stuck_timer - 1)
        
        # Update total distance
        self.total_distance += math.sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
    
    def check_collision(self, obstacles):
        car_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                               self.width, self.height)
        for obs in obstacles:
            obs_rect = pygame.Rect(obs.x, obs.y, obs.width, obs.height)
            if car_rect.colliderect(obs_rect):
                return obs
        return None
    
    def check_checkpoint(self, checkpoints, start_finish_line):
        if self.finished:
            return False
        
        # Get the next checkpoint we need to reach
        next_checkpoint_idx = self.checkpoint_index % len(checkpoints)
        target = checkpoints[next_checkpoint_idx]
        dist = math.sqrt((self.x - target.x)**2 + (self.y - target.y)**2)
        
        # Check if we've hit the checkpoint
        if dist < target.radius:
            # Only count it if we're passing them in order
            if next_checkpoint_idx == self.last_checkpoint_passed + 1 or \
               (self.last_checkpoint_passed == len(checkpoints) - 1 and next_checkpoint_idx == 0):
                self.checkpoint_index += 1
                self.last_checkpoint_passed = next_checkpoint_idx
                if not self.is_player:
                    self.target_checkpoint = self.checkpoint_index
        
        # Check if we've passed all checkpoints and can now cross the finish line
        if self.last_checkpoint_passed == len(checkpoints) - 1 and start_finish_line:
            # Check if we're crossing the start/finish line
            if self.check_finish_line_crossing(start_finish_line):
                self.lap += 1
                self.last_checkpoint_passed = -1  # Reset for next lap
                self.checkpoint_index = self.lap * len(checkpoints)  # Update for position tracking
                
                # Refill boost for new lap!
                self.boost_available = 2
                
                if self.lap >= 3:
                    self.finished = True
                    return True
        
        return False
    
    def check_finish_line_crossing(self, finish_line):
        """Check if car is crossing the start/finish line"""
        # Simple rectangle intersection check
        car_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                              self.width, self.height)
        
        # For now, using a simple rectangular finish line
        finish_rect = pygame.Rect(finish_line.x, finish_line.y,
                                  finish_line.width, finish_line.height)
        
        return car_rect.colliderect(finish_rect)
    
    def draw(self, screen):
        # Draw boost flames if boosting
        if self.is_boosting and self.is_player:
            rad = math.radians(self.angle)
            # Draw flames behind the car
            flame_length = 15 + random.randint(-3, 3)
            for i in range(3):
                flame_x = self.x - math.sin(rad) * (self.height//2 + 5 + i * 5)
                flame_y = self.y + math.cos(rad) * (self.height//2 + 5 + i * 5)
                flame_offset = random.randint(-5, 5)
                flame_x += math.cos(rad) * flame_offset
                flame_y += math.sin(rad) * flame_offset
                
                flame_color = ORANGE if i % 2 == 0 else YELLOW
                flame_size = 6 - i * 2
                pygame.draw.circle(screen, flame_color, 
                                 (int(flame_x), int(flame_y)), flame_size)
        
        # Draw shadow if jumping
        if self.is_jumping and self.jump_height > 0:
            shadow_offset = self.jump_height // 2
            rad = math.radians(self.angle)
            corners = [
                (-self.width//2, -self.height//2),
                (self.width//2, -self.height//2),
                (self.width//2, self.height//2),
                (-self.width//2, self.height//2)
            ]
            
            shadow_corners = []
            for cx, cy in corners:
                rx = cx * math.cos(rad) - cy * math.sin(rad)
                ry = cx * math.sin(rad) + cy * math.cos(rad)
                shadow_corners.append((self.x + rx, self.y + ry + shadow_offset))
            
            pygame.draw.polygon(screen, (100, 100, 100, 128), shadow_corners)
        
        # Draw car as rotated rectangle (offset by jump height)
        rad = math.radians(self.angle)
        corners = [
            (-self.width//2, -self.height//2),
            (self.width//2, -self.height//2),
            (self.width//2, self.height//2),
            (-self.width//2, self.height//2)
        ]
        
        rotated_corners = []
        for cx, cy in corners:
            rx = cx * math.cos(rad) - cy * math.sin(rad)
            ry = cx * math.sin(rad) + cy * math.cos(rad)
            rotated_corners.append((self.x + rx, self.y + ry - self.jump_height))
        
        pygame.draw.polygon(screen, self.color, rotated_corners)
        pygame.draw.polygon(screen, BLACK, rotated_corners, 2)
        
        # Draw direction indicator
        front_x = self.x + math.sin(rad) * self.height // 2
        front_y = self.y - math.cos(rad) * self.height // 2 - self.jump_height
        pygame.draw.circle(screen, WHITE, (int(front_x), int(front_y)), 3)

class Track:
    def __init__(self, name, checkpoints, obstacles, start_positions, markers=None, start_finish_line=None):
        self.name = name
        self.checkpoints = checkpoints
        self.obstacles = obstacles
        self.start_positions = start_positions
        self.markers = markers or []
        self.start_finish_line = start_finish_line

def create_desk_track():
    """Cluttered desk circuit"""
    checkpoints = [
        Checkpoint(200, 400, 50),
        Checkpoint(300, 200, 50),
        Checkpoint(600, 150, 50),
        Checkpoint(900, 250, 50),
        Checkpoint(1000, 500, 50),
        Checkpoint(800, 650, 50),
        Checkpoint(500, 600, 50),
        Checkpoint(300, 500, 50),
    ]
    
    obstacles = [
        # Coffee mug
        Obstacle(400, 300, 60, 60, BROWN, "Coffee"),
        # Keyboard
        Obstacle(600, 400, 200, 80, DARK_GRAY, "Keyboard"),
        # Mouse
        Obstacle(500, 250, 50, 70, GRAY, "Mouse"),
        # Notepad
        Obstacle(750, 550, 120, 150, YELLOW, "Notes"),
        # Pen holder
        Obstacle(250, 250, 50, 50, BLUE, "Pens"),
        # Stapler
        Obstacle(850, 400, 80, 40, BLACK, "Stapler"),
        # Phone
        Obstacle(350, 600, 70, 120, BLACK, "Phone"),
    ]
    
    start_positions = [
        (150, 400, 0), (150, 430, 0), (150, 460, 0), (150, 490, 0)
    ]
    
    # Paper clips showing track outline
    markers = []
    # Inner edge markers (closer to obstacles)
    inner_path = [
        (160, 350), (180, 320), (200, 280), (230, 240), (270, 210),
        (320, 180), (380, 160), (450, 150), (520, 145), (590, 140),
        (660, 145), (730, 155), (800, 170), (860, 200), (910, 240),
        (950, 290), (980, 340), (1000, 390), (1010, 450), (1010, 510),
        (1000, 560), (980, 610), (950, 650), (900, 680), (840, 695),
        (780, 700), (720, 695), (660, 685), (600, 670), (540, 650),
        (480, 625), (420, 595), (370, 560), (330, 525), (290, 490),
        (260, 455), (240, 420), (220, 385), (200, 350), (180, 320),
    ]
    
    for i, (x, y) in enumerate(inner_path):
        markers.append(TrackMarker(x, y, "paperclip", rotation=i * 9))
    
    # Outer edge markers (track boundaries)
    outer_path = [
        (120, 330), (100, 280), (100, 230), (110, 180), (140, 140),
        (200, 110), (280, 90), (370, 80), (470, 75), (570, 75),
        (670, 80), (760, 95), (840, 120), (910, 160), (970, 210),
        (1020, 270), (1050, 340), (1060, 420), (1060, 500), (1050, 580),
        (1025, 650), (980, 710), (920, 750), (850, 770), (770, 775),
        (680, 770), (590, 755), (510, 730), (440, 700), (380, 665),
        (330, 625), (285, 580), (245, 535), (210, 490), (180, 445),
        (155, 400), (135, 355),
    ]
    
    for i, (x, y) in enumerate(outer_path):
        markers.append(TrackMarker(x, y, "paperclip", rotation=i * 7))
    
    # Start/Finish Line (vertical line near starting position)
    start_finish = StartFinishLine(x=140, y=350, width=10, height=100, angle=0)
    
    return Track("Desk Circuit", checkpoints, obstacles, start_positions, markers, start_finish)

def create_living_room_track():
    """Living room circuit"""
    checkpoints = [
        Checkpoint(300, 600, 50),
        Checkpoint(250, 300, 50),
        Checkpoint(500, 200, 50),
        Checkpoint(750, 250, 50),
        Checkpoint(950, 400, 50),
        Checkpoint(900, 650, 50),
        Checkpoint(600, 700, 50),
    ]
    
    obstacles = [
        # Couch
        Obstacle(400, 400, 250, 120, BROWN, "Couch"),
        # Coffee table
        Obstacle(550, 550, 150, 100, WOOD, "Table"),
        # TV stand
        Obstacle(800, 150, 180, 60, BLACK, "TV"),
        # Armchair
        Obstacle(200, 450, 100, 100, ORANGE, "Chair"),
        # Plant pot
        Obstacle(950, 550, 60, 60, GREEN, "Plant"),
        # Rug (just visual, not collision)
        # Lamp
        Obstacle(300, 200, 40, 40, YELLOW, "Lamp"),
        # Bookshelf
        Obstacle(100, 150, 80, 200, WOOD, "Books"),
    ]
    
    start_positions = [
        (300, 650, 90), (300, 680, 90), (330, 650, 90), (330, 680, 90)
    ]
    
    # Socks showing track outline!
    markers = []
    
    # Inner edge
    inner_path = [
        (320, 560), (310, 510), (290, 460), (270, 410), (260, 360),
        (260, 310), (265, 260), (280, 220), (310, 190), (350, 175),
        (400, 170), (450, 175), (510, 185), (570, 200), (630, 220),
        (690, 245), (750, 275), (800, 310), (850, 350), (900, 390),
        (940, 435), (970, 485), (985, 540), (985, 595), (970, 645),
        (940, 685), (890, 710), (830, 720), (770, 720), (710, 715),
        (650, 705), (590, 690), (530, 675), (470, 660), (410, 650),
        (360, 640), (320, 620), (295, 590),
    ]
    
    for i, (x, y) in enumerate(inner_path):
        markers.append(TrackMarker(x, y, "sock", rotation=i * 10))
    
    # Outer edge
    outer_path = [
        (270, 710), (250, 670), (240, 620), (230, 560), (220, 500),
        (215, 440), (210, 380), (210, 320), (215, 260), (225, 210),
        (245, 170), (275, 140), (320, 120), (380, 110), (450, 108),
        (520, 115), (590, 130), (660, 155), (725, 185), (785, 225),
        (840, 270), (890, 320), (935, 375), (975, 430), (1005, 490),
        (1020, 555), (1025, 620), (1015, 680), (990, 730), (950, 765),
        (895, 785), (830, 790), (760, 785), (690, 775), (625, 760),
        (565, 740), (510, 720), (455, 700), (400, 685), (345, 675),
        (295, 670),
    ]
    
    for i, (x, y) in enumerate(outer_path):
        markers.append(TrackMarker(x, y, "sock", rotation=i * 8))
    
    # Start/Finish Line (horizontal line near starting position)
    start_finish = StartFinishLine(x=260, y=665, width=100, height=10, angle=0)
    
    return Track("Living Room", checkpoints, obstacles, start_positions, markers, start_finish)

def create_garden_track():
    """Garden circuit with pond, shed, patio and jump"""
    checkpoints = [
        Checkpoint(200, 650, 50),
        Checkpoint(200, 400, 50),
        Checkpoint(350, 250, 50),
        Checkpoint(600, 200, 50),
        Checkpoint(850, 300, 50),
        Checkpoint(950, 500, 50),
        Checkpoint(800, 650, 50),
        Checkpoint(500, 700, 50),
    ]
    
    obstacles = [
        # Pond
        Obstacle(400, 400, 200, 150, WATER_BLUE, "Pond"),
        # Shed
        Obstacle(750, 150, 150, 120, BROWN, "Shed"),
        # Patio stones
        Obstacle(250, 550, 120, 120, STONE_GRAY, "Patio"),
        # Garden table
        Obstacle(550, 500, 100, 80, WOOD, "Table"),
        # Garden chairs
        Obstacle(500, 600, 50, 50, GREEN, "Chair"),
        Obstacle(650, 550, 50, 50, GREEN, "Chair"),
        # Plant pots
        Obstacle(900, 200, 40, 40, ORANGE, "Pot"),
        Obstacle(350, 350, 40, 40, ORANGE, "Pot"),
        # BBQ Grill
        Obstacle(150, 250, 60, 60, BLACK, "BBQ"),
        # Steps (JUMP!)
        Obstacle(650, 300, 80, 40, STONE_GRAY, "JUMP!", is_jump=True),
    ]
    
    start_positions = [
        (150, 650, 90), (150, 680, 90), (180, 650, 90), (180, 680, 90)
    ]
    
    # Flowers showing track outline!
    markers = []
    
    # Inner edge
    inner_path = [
        (170, 610), (175, 560), (180, 510), (185, 460), (188, 410),
        (190, 360), (195, 310), (205, 270), (225, 235), (255, 210),
        (295, 190), (340, 180), (390, 175), (445, 175), (500, 180),
        (555, 190), (610, 205), (665, 225), (715, 250), (760, 280),
        (800, 315), (835, 355), (865, 400), (890, 450), (910, 500),
        (925, 550), (930, 600), (925, 645), (910, 685), (880, 715),
        (840, 735), (790, 745), (735, 745), (680, 740), (625, 730),
        (570, 715), (520, 700), (470, 690), (420, 685), (370, 685),
        (320, 690), (275, 695), (230, 695), (190, 685), (160, 665),
    ]
    
    for i, (x, y) in enumerate(inner_path):
        markers.append(TrackMarker(x, y, "flower", rotation=i * 8))
    
    # Outer edge
    outer_path = [
        (120, 695), (110, 655), (105, 610), (102, 560), (100, 505),
        (100, 450), (102, 395), (108, 340), (120, 290), (140, 245),
        (170, 205), (210, 170), (260, 145), (320, 125), (390, 115),
        (465, 110), (540, 110), (615, 118), (685, 135), (750, 160),
        (810, 195), (865, 240), (915, 295), (955, 355), (985, 420),
        (1005, 490), (1015, 560), (1015, 625), (1005, 685), (980, 735),
        (945, 775), (895, 800), (835, 815), (770, 820), (700, 818),
        (630, 810), (565, 795), (505, 775), (450, 755), (400, 735),
        (355, 720), (310, 710), (265, 705), (220, 705), (175, 710),
        (135, 720),
    ]
    
    for i, (x, y) in enumerate(outer_path):
        markers.append(TrackMarker(x, y, "flower", rotation=i * 7))
    
    # Start/Finish Line (horizontal line near starting position)
    start_finish = StartFinishLine(x=110, y=670, width=100, height=10, angle=0)
    
    return Track("Garden Circuit", checkpoints, obstacles, start_positions, markers, start_finish)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Top-Down Racing")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.tracks = [create_desk_track(), create_living_room_track(), create_garden_track()]
        self.current_track_index = 0
        
        self.state = "menu"  # menu, racing, results, championship
        self.cars = []
        self.player_points = 0
        self.race_results = []
        
        # Championship mode
        self.championship_mode = False
        self.championship_races_completed = []
        self.championship_results = []
        
    def start_race(self):
        self.state = "racing"
        track = self.tracks[self.current_track_index]
        self.cars = []
        
        # Create player car
        start = track.start_positions[0]
        player = Car(start[0], start[1], RED, is_player=True)
        player.angle = start[2]
        self.cars.append(player)
        
        # Create AI cars
        ai_colors = [BLUE, GREEN, YELLOW]
        for i, color in enumerate(ai_colors):
            start = track.start_positions[i + 1]
            ai_car = Car(start[0], start[1], color)
            ai_car.angle = start[2]
            self.cars.append(ai_car)
        
        self.race_results = []
    
    def update_race(self, keys):
        track = self.tracks[self.current_track_index]
        
        # Update cars
        for car in self.cars:
            if car.is_player:
                car.update_player(keys, track.obstacles)
            else:
                car.update_ai(track.checkpoints, track.obstacles, self.cars)
            
            # Check checkpoints
            if car.check_checkpoint(track.checkpoints, track.start_finish_line):
                # Car finished
                if car.finish_position is None:
                    car.finish_position = len(self.race_results) + 1
                    self.race_results.append(car)
        
        # Check if all cars finished
        if len(self.race_results) == len(self.cars):
            # Award points (1st: 25, 2nd: 18, 3rd: 15, 4th: 12)
            points = [25, 18, 15, 12]
            if self.cars[0].finish_position and self.cars[0].finish_position <= 4:
                points_earned = points[self.cars[0].finish_position - 1]
                self.player_points += points_earned
                
                # Track championship progress
                if self.championship_mode:
                    track_name = self.tracks[self.current_track_index].name
                    self.championship_races_completed.append(track_name)
                    self.championship_results.append({
                        'track': track_name,
                        'position': self.cars[0].finish_position,
                        'points': points_earned
                    })
            
            # Check if championship is complete
            if self.championship_mode and len(self.championship_races_completed) >= 3:
                self.state = "championship"
            else:
                self.state = "results"
    
    def draw_track_marker(self, screen, marker):
        """Draw a track edge marker"""
        if marker.marker_type == "paperclip":
            # Silver paperclip
            color = (192, 192, 192)
            # Draw paperclip as two loops
            rad = math.radians(marker.rotation)
            
            # Main body
            points = []
            for angle in range(0, 360, 30):
                a = math.radians(angle)
                x = marker.x + math.cos(a + rad) * 8 + math.cos(rad) * 3
                y = marker.y + math.sin(a + rad) * 8 + math.sin(rad) * 3
                points.append((x, y))
            pygame.draw.polygon(screen, color, points, 2)
            
            # Inner loop
            points2 = []
            for angle in range(0, 360, 40):
                a = math.radians(angle)
                x = marker.x + math.cos(a + rad) * 4
                y = marker.y + math.sin(a + rad) * 4
                points2.append((x, y))
            pygame.draw.polygon(screen, color, points2, 2)
            
        elif marker.marker_type == "sock":
            # Colorful sock - randomly pick bright colors
            colors = [(255, 100, 100), (100, 100, 255), (100, 255, 100), 
                     (255, 255, 100), (255, 100, 255), (100, 255, 255)]
            color = colors[int(marker.x + marker.y) % len(colors)]
            
            rad = math.radians(marker.rotation)
            
            # Sock body
            sock_points = [
                (-3, -10), (3, -10), (4, 5), (6, 8), (5, 10),
                (-5, 10), (-6, 8), (-4, 5)
            ]
            
            rotated = []
            for px, py in sock_points:
                rx = px * math.cos(rad) - py * math.sin(rad)
                ry = px * math.sin(rad) + py * math.cos(rad)
                rotated.append((marker.x + rx, marker.y + ry))
            
            pygame.draw.polygon(screen, color, rotated)
            pygame.draw.polygon(screen, BLACK, rotated, 1)
            
            # Heel
            heel_x = marker.x + math.cos(rad + math.pi/2) * 4
            heel_y = marker.y + math.sin(rad + math.pi/2) * 4
            pygame.draw.circle(screen, color, (int(heel_x), int(heel_y)), 3)
            
        elif marker.marker_type == "flower":
            # Colorful flower
            petal_colors = [(255, 100, 150), (255, 200, 100), (150, 100, 255),
                           (255, 150, 200), (255, 255, 100)]
            color = petal_colors[int(marker.x + marker.y) % len(petal_colors)]
            center_color = (255, 220, 0)
            
            # Draw petals
            for i in range(5):
                angle = math.radians(i * 72 + marker.rotation)
                petal_x = marker.x + math.cos(angle) * 6
                petal_y = marker.y + math.sin(angle) * 6
                pygame.draw.circle(screen, color, (int(petal_x), int(petal_y)), 4)
            
            # Draw center
            pygame.draw.circle(screen, center_color, (int(marker.x), int(marker.y)), 4)
            pygame.draw.circle(screen, BLACK, (int(marker.x), int(marker.y)), 4, 1)
    
    def draw_track(self):
        track = self.tracks[self.current_track_index]
        
        # Background
        if track.name == "Desk Circuit":
            self.screen.fill(WOOD)
        elif track.name == "Living Room":
            self.screen.fill((220, 220, 200))
        else:  # Garden
            self.screen.fill(GRASS_GREEN)
        
        # Draw track markers (paper clips, socks, flowers) FIRST
        for marker in track.markers:
            self.draw_track_marker(self.screen, marker)
        
        # Draw start/finish line
        if track.start_finish_line:
            sf = track.start_finish_line
            # Draw checkered pattern
            pygame.draw.rect(self.screen, WHITE, (sf.x, sf.y, sf.width, sf.height))
            pygame.draw.rect(self.screen, BLACK, (sf.x, sf.y, sf.width, sf.height), 3)
            
            # Add checkered flag pattern
            checker_size = 10
            for i in range(int(sf.width // checker_size) + 1):
                for j in range(int(sf.height // checker_size) + 1):
                    if (i + j) % 2 == 0:
                        pygame.draw.rect(self.screen, BLACK,
                                       (sf.x + i * checker_size,
                                        sf.y + j * checker_size,
                                        checker_size, checker_size))
        
        # Draw checkpoints (subtle)
        for i, cp in enumerate(track.checkpoints):
            # Highlight the player's next checkpoint
            player = self.cars[0] if self.cars else None
            if player:
                next_cp_idx = player.checkpoint_index % len(track.checkpoints)
                if i == next_cp_idx:
                    # Next checkpoint - make it very visible
                    color = YELLOW
                    width = 4
                else:
                    color = GREEN if i == 0 else LIGHT_BLUE
                    width = 2
            else:
                color = GREEN if i == 0 else LIGHT_BLUE
                width = 2
            
            pygame.draw.circle(self.screen, color, (int(cp.x), int(cp.y)), 
                             int(cp.radius), width)
        
        # Draw obstacles
        for obs in track.obstacles:
            pygame.draw.rect(self.screen, obs.color, 
                           (obs.x, obs.y, obs.width, obs.height))
            
            # Draw jump ramps with special indicator
            if obs.is_jump:
                pygame.draw.rect(self.screen, YELLOW, 
                               (obs.x, obs.y, obs.width, obs.height), 3)
                # Draw ramp lines
                for i in range(3):
                    y_pos = obs.y + (i + 1) * obs.height // 4
                    pygame.draw.line(self.screen, BLACK, 
                                   (obs.x, y_pos), (obs.x + obs.width, y_pos), 2)
            else:
                pygame.draw.rect(self.screen, BLACK, 
                               (obs.x, obs.y, obs.width, obs.height), 2)
            
            if obs.label:
                label = self.small_font.render(obs.label, True, WHITE if not obs.is_jump else BLACK)
                label_rect = label.get_rect(center=(obs.x + obs.width//2, 
                                                    obs.y + obs.height//2))
                self.screen.blit(label, label_rect)
    
    def draw_hud(self):
        player = self.cars[0]
        track = self.tracks[self.current_track_index]
        
        # Lap counter
        lap_text = self.font.render(f"Lap: {player.lap + 1}/3", True, BLACK)
        self.screen.blit(lap_text, (10, 10))
        
        # Checkpoint progress
        next_cp = (player.checkpoint_index % len(track.checkpoints)) + 1
        total_cps = len(track.checkpoints)
        
        # Show different message if all checkpoints passed
        if player.last_checkpoint_passed == total_cps - 1:
            cp_text = self.small_font.render(f"Cross FINISH LINE!", True, GREEN)
        else:
            cp_text = self.small_font.render(f"Next CP: {next_cp}/{total_cps}", True, BLACK)
        self.screen.blit(cp_text, (10, 45))
        
        # Position
        position = sum(1 for car in self.cars if car.lap > player.lap or 
                      (car.lap == player.lap and car.checkpoint_index > player.checkpoint_index)
                      or (car.lap == player.lap and car.checkpoint_index == player.checkpoint_index 
                          and car.total_distance > player.total_distance)) + 1
        
        pos_text = self.font.render(f"Position: {position}/4", True, BLACK)
        self.screen.blit(pos_text, (10, 75))
        
        # Boost indicator
        boost_text = self.small_font.render(f"Boost: {player.boost_available}", True, BLACK)
        self.screen.blit(boost_text, (10, 110))
        
        # Draw boost icons
        for i in range(player.boost_available):
            icon_x = 10 + i * 35
            icon_y = 140
            # Draw lightning bolt icon
            pygame.draw.polygon(self.screen, YELLOW, [
                (icon_x + 15, icon_y),
                (icon_x + 10, icon_y + 12),
                (icon_x + 18, icon_y + 12),
                (icon_x + 10, icon_y + 25),
                (icon_x + 20, icon_y + 8),
                (icon_x + 12, icon_y + 8)
            ])
            pygame.draw.polygon(self.screen, BLACK, [
                (icon_x + 15, icon_y),
                (icon_x + 10, icon_y + 12),
                (icon_x + 18, icon_y + 12),
                (icon_x + 10, icon_y + 25),
                (icon_x + 20, icon_y + 8),
                (icon_x + 12, icon_y + 8)
            ], 2)
        
        # Boosting indicator
        if player.is_boosting:
            boosting_text = self.font.render("BOOSTING!", True, ORANGE)
            boost_rect = boosting_text.get_rect(center=(SCREEN_WIDTH//2, 50))
            # Pulsing effect
            pulse = int(abs(math.sin(pygame.time.get_ticks() / 100) * 20))
            pygame.draw.rect(self.screen, YELLOW, 
                           (boost_rect.x - 10 - pulse, boost_rect.y - 5,
                            boost_rect.width + 20 + pulse*2, boost_rect.height + 10), 0)
            pygame.draw.rect(self.screen, BLACK, 
                           (boost_rect.x - 10 - pulse, boost_rect.y - 5,
                            boost_rect.width + 20 + pulse*2, boost_rect.height + 10), 3)
            self.screen.blit(boosting_text, boost_rect)
        
        # Points
        points_text = self.font.render(f"Points: {self.player_points}", True, BLACK)
        self.screen.blit(points_text, (10, 180))
        
        # Track name
        track_text = self.small_font.render(self.tracks[self.current_track_index].name, 
                                           True, BLACK)
        self.screen.blit(track_text, (SCREEN_WIDTH - 200, 10))
    
    def draw_menu(self):
        self.screen.fill(DARK_GRAY)
        
        title = self.font.render("TOP-DOWN RACING", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        # Mode selection
        mode_text = "CHAMPIONSHIP MODE" if self.championship_mode else "SINGLE RACE"
        mode = self.font.render(mode_text, True, YELLOW if self.championship_mode else WHITE)
        mode_rect = mode.get_rect(center=(SCREEN_WIDTH//2, 230))
        self.screen.blit(mode, mode_rect)
        
        mode_hint = self.small_font.render("Press C to toggle mode", True, WHITE)
        mode_hint_rect = mode_hint.get_rect(center=(SCREEN_WIDTH//2, 270))
        self.screen.blit(mode_hint, mode_hint_rect)
        
        # Track selection (only for single race)
        if not self.championship_mode:
            track_text = self.font.render(f"Track: {self.tracks[self.current_track_index].name}", 
                                         True, WHITE)
            track_rect = track_text.get_rect(center=(SCREEN_WIDTH//2, 340))
            self.screen.blit(track_text, track_rect)
            
            arrow_left = self.font.render("<", True, WHITE)
            arrow_right = self.font.render(">", True, WHITE)
            self.screen.blit(arrow_left, (SCREEN_WIDTH//2 - 250, 330))
            self.screen.blit(arrow_right, (SCREEN_WIDTH//2 + 230, 330))
        else:
            champ_info = self.small_font.render("Race all 3 tracks for the championship!", True, GREEN)
            champ_rect = champ_info.get_rect(center=(SCREEN_WIDTH//2, 340))
            self.screen.blit(champ_info, champ_rect)
        
        # Instructions
        instructions = [
            "Arrow Keys to Drive",
            "SPACE to Boost (2x per lap)",
            "Press SPACE to Start",
            "First to 3 laps wins!",
            f"Total Points: {self.player_points}"
        ]
        
        y = 420
        for text in instructions:
            rendered = self.small_font.render(text, True, WHITE)
            rect = rendered.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(rendered, rect)
            y += 40
    
    def draw_results(self):
        self.screen.fill(DARK_GRAY)
        
        title = self.font.render("RACE RESULTS", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Results
        y = 200
        positions = ["1st", "2nd", "3rd", "4th"]
        points = [25, 18, 15, 12]
        
        for i, car in enumerate(self.race_results):
            color_name = "You" if car.is_player else ["Blue Car", "Green Car", "Yellow Car"][
                [c for c in self.cars if not c.is_player].index(car)]
            
            result_text = f"{positions[i]}: {color_name}"
            if i < 3:
                result_text += f" (+{points[i]} points)"
            
            color = car.color if not car.is_player else WHITE
            text = self.font.render(result_text, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text, rect)
            y += 50
        
        # Total points
        total = self.font.render(f"Total Points: {self.player_points}", True, WHITE)
        total_rect = total.get_rect(center=(SCREEN_WIDTH//2, y + 50))
        self.screen.blit(total, total_rect)
        
        # Continue hint
        if self.championship_mode and len(self.championship_races_completed) < 3:
            continue_text = self.small_font.render(
                f"Press SPACE for next race ({len(self.championship_races_completed)}/3 complete)", 
                True, GREEN)
        else:
            continue_text = self.small_font.render("Press SPACE to continue", True, WHITE)
        
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_championship_results(self):
        self.screen.fill(DARK_GRAY)
        
        # Title
        title = self.font.render("CHAMPIONSHIP COMPLETE!", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title, title_rect)
        
        # Draw trophy
        self.draw_trophy(SCREEN_WIDTH//2, 180)
        
        # League table
        table_title = self.font.render("FINAL STANDINGS", True, WHITE)
        table_rect = table_title.get_rect(center=(SCREEN_WIDTH//2, 320))
        self.screen.blit(table_title, table_rect)
        
        # Show each race result
        y = 380
        for result in self.championship_results:
            positions = ["1st", "2nd", "3rd", "4th"]
            pos_text = positions[result['position'] - 1]
            
            race_text = f"{result['track']}: {pos_text} (+{result['points']} pts)"
            text = self.small_font.render(race_text, True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text, rect)
            y += 35
        
        # Total score
        y += 20
        total_text = self.font.render(f"TOTAL: {self.player_points} POINTS", True, YELLOW)
        total_rect = total_text.get_rect(center=(SCREEN_WIDTH//2, y))
        self.screen.blit(total_text, total_rect)
        
        # Championship result
        y += 60
        if self.player_points >= 60:  # Average of 20 points per race
            verdict = "CHAMPION!"
            verdict_color = YELLOW
        elif self.player_points >= 45:
            verdict = "Great Performance!"
            verdict_color = GREEN
        else:
            verdict = "Better luck next time!"
            verdict_color = WHITE
        
        verdict_text = self.font.render(verdict, True, verdict_color)
        verdict_rect = verdict_text.get_rect(center=(SCREEN_WIDTH//2, y))
        self.screen.blit(verdict_text, verdict_rect)
        
        # Continue
        continue_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_trophy(self, x, y):
        """Draw a simple trophy"""
        # Cup
        pygame.draw.ellipse(self.screen, YELLOW, (x - 40, y - 30, 80, 60))
        pygame.draw.rect(self.screen, YELLOW, (x - 35, y, 70, 40))
        
        # Handles
        pygame.draw.arc(self.screen, YELLOW, (x - 60, y - 10, 30, 40), 0, 3.14, 5)
        pygame.draw.arc(self.screen, YELLOW, (x + 30, y - 10, 30, 40), 0, 3.14, 5)
        
        # Base
        pygame.draw.rect(self.screen, YELLOW, (x - 45, y + 40, 90, 10))
        pygame.draw.rect(self.screen, YELLOW, (x - 35, y + 50, 70, 15))
        
        # Outlines
        pygame.draw.ellipse(self.screen, BLACK, (x - 40, y - 30, 80, 60), 3)
        pygame.draw.rect(self.screen, BLACK, (x - 35, y, 70, 40), 3)
        pygame.draw.arc(self.screen, BLACK, (x - 60, y - 10, 30, 40), 0, 3.14, 5)
        pygame.draw.arc(self.screen, BLACK, (x + 30, y - 10, 30, 40), 0, 3.14, 5)
        pygame.draw.rect(self.screen, BLACK, (x - 45, y + 40, 90, 10), 3)
        pygame.draw.rect(self.screen, BLACK, (x - 35, y + 50, 70, 15), 3)
    
    def run(self):
        running = True
        
        while running:
            keys = pygame.key.get_pressed()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_SPACE:
                            if self.championship_mode:
                                # Start championship from first track
                                self.current_track_index = 0
                                self.championship_races_completed = []
                                self.championship_results = []
                                self.player_points = 0
                            self.start_race()
                        elif event.key == pygame.K_LEFT and not self.championship_mode:
                            self.current_track_index = (self.current_track_index - 1) % len(self.tracks)
                        elif event.key == pygame.K_RIGHT and not self.championship_mode:
                            self.current_track_index = (self.current_track_index + 1) % len(self.tracks)
                        elif event.key == pygame.K_c:
                            self.championship_mode = not self.championship_mode
                    
                    elif self.state == "results":
                        if event.key == pygame.K_SPACE:
                            if self.championship_mode and len(self.championship_races_completed) < 3:
                                # Move to next track in championship
                                self.current_track_index = (self.current_track_index + 1) % len(self.tracks)
                                self.start_race()
                            else:
                                self.state = "menu"
                                self.championship_mode = False
                    
                    elif self.state == "championship":
                        if event.key == pygame.K_SPACE:
                            self.state = "menu"
                            self.championship_mode = False
                            self.championship_races_completed = []
                            self.championship_results = []
            
            # Update
            if self.state == "racing":
                self.update_race(keys)
            
            # Draw
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "racing":
                self.draw_track()
                for car in self.cars:
                    car.draw(self.screen)
                self.draw_hud()
            elif self.state == "results":
                self.draw_results()
            elif self.state == "championship":
                self.draw_championship_results()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
