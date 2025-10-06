import pygame
import math
import random
import numpy as np

# Initialize pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
WIDTH, HEIGHT = 1280, 720
FPS = 60
DEEP_BLUE = (10, 20, 60)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CubeStream")
clock = pygame.time.Clock()

# Generate chiptune melody with transpose
def generate_chiptune(transpose=0):
    sample_rate = 22050
    duration = 8  # Slower tempo - doubled duration
    # Mystical minor melody - lower register, flowing intervals
    notes = [220, 247, 262, 294, 330, 294, 262, 247]  # A, B, C, D, E, D, C, B
    note_duration = duration / len(notes)

    # Apply transpose (semitones)
    transpose_factor = 2 ** (transpose / 12.0)
    transposed_notes = [note * transpose_factor for note in notes]

    samples = np.array([], dtype=np.int16)

    for note in transposed_notes:
        t = np.linspace(0, note_duration, int(sample_rate * note_duration), False)
        # Softer sine wave base for mystical sound
        wave = np.sin(note * 2 * np.pi * t)
        # Add subtle harmonics
        wave += 0.3 * np.sin(note * 3 * np.pi * t)
        wave += 0.2 * np.sin(note * 5 * np.pi * t)

        # Gentler envelope for sustained mystical tone
        envelope = np.exp(-1.5 * t / note_duration)
        wave = wave * envelope * 0.25

        # Convert to int16
        wave = np.int16(wave * 32767 / (np.max(np.abs(wave)) + 0.001))
        samples = np.concatenate([samples, wave])

    # Stereo
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

# Start music
music_channel = None
try:
    chiptune = generate_chiptune()
    music_channel = chiptune.play(3)  # Play 4 times total (1 + 3 loops)
except Exception as e:
    print(f"Music disabled: {e}")

# 3D Cube vertices
cube_vertices = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
]

# Cube edges
cube_edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]

# Particle class (simplified - no alpha)
class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        angle = random.uniform(0, 2 * math.pi)
        elevation = random.uniform(-math.pi/2, math.pi/2)
        # Keep particles near cube, away from camera
        distance = random.uniform(100, 180)

        self.x = math.cos(angle) * math.cos(elevation) * distance + WIDTH / 2
        self.y = math.sin(elevation) * distance + HEIGHT / 2
        self.z = math.sin(angle) * math.cos(elevation) * distance

        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, 0.3)
        self.vz = random.uniform(-0.3, 0.3)

        # Subtle complementary colors - muted blues, purples, teals
        colors = [
            (60, 80, 120),   # Muted blue
            (70, 60, 110),   # Muted purple
            (50, 90, 100),   # Muted teal
            (65, 75, 115)    # Muted blue-purple
        ]
        self.color = random.choice(colors)
        self.size = random.randint(1, 2)
        self.life = random.randint(240, 360)  # Longer life for smoother fades
        self.max_life = self.life
        self.color_shift = random.uniform(0, 2 * math.pi)  # For subtle color animation

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.life -= 1
        self.color_shift += 0.02  # Slow color shift
        if self.life <= 0:
            self.reset()

    def draw(self, screen):
        # Smooth fade with easing
        fade = (self.life / self.max_life) ** 0.5  # Square root for smoother fade

        # Subtle color shift
        shift = math.sin(self.color_shift) * 0.15  # Small shift amount
        color = tuple(int(c * fade * (1 + shift * 0.5)) for c in self.color)
        color = tuple(max(0, min(255, c)) for c in color)  # Clamp

        # Simple depth-based sizing
        scale = 200 / (200 + self.z)
        size = max(1, int(self.size * scale))

        # Draw directly without alpha surface
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)

# Create particles - fewer for less flicker
particles = [Particle() for _ in range(70)]

# Rotation angles
angle_x = 0
angle_y = 0
angle_z = 0

# Project 3D to 2D
def project(vertex, ax, ay, az, scale=80):
    x, y, z = vertex

    # Rotate X
    cos_x, sin_x = math.cos(ax), math.sin(ax)
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

    # Rotate Y
    cos_y, sin_y = math.cos(ay), math.sin(ay)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y

    # Rotate Z
    cos_z, sin_z = math.cos(az), math.sin(az)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z

    # Project
    factor = 200 / (200 + z * scale)
    x_proj = x * scale * factor + WIDTH / 2
    y_proj = y * scale * factor + HEIGHT / 2

    return int(x_proj), int(y_proj), z

# Main loop
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Check if music needs to restart with new transpose
    if music_channel and not music_channel.get_busy():
        try:
            transpose = random.randint(-7, 7)  # Random transpose within ±7 semitones
            chiptune = generate_chiptune(transpose)
            music_channel = chiptune.play(3)  # Play 4 times before switching again
        except Exception as e:
            pass

    # Clear screen
    screen.fill(DEEP_BLUE)

    # Update rotation
    angle_x += 0.01
    angle_y += 0.015
    angle_z += 0.008

    # Update and draw particles
    for particle in particles:
        particle.update()
        particle.draw(screen)

    # Project cube
    projected = []
    for vertex in cube_vertices:
        x, y, z = project(vertex, angle_x, angle_y, angle_z)
        projected.append((x, y, z))

    # Draw cube edges
    for v1, v2 in cube_edges:
        brightness = int(150 + projected[v1][2] * 0.5)
        brightness = max(50, min(255, brightness))
        color = (brightness, brightness, 255)
        pygame.draw.line(screen, color,
                        (projected[v1][0], projected[v1][1]),
                        (projected[v2][0], projected[v2][1]), 3)

    # Draw vertices
    for x, y, z in projected:
        pygame.draw.circle(screen, (200, 200, 255), (x, y), 5)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
