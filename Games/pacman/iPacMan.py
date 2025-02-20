import pygame
import random
import sys

# -----------------------------------------------------------------------------
# Game Constants
# -----------------------------------------------------------------------------
TILE_SIZE = 24
FPS = 10

# Colors
BLACK  = (0, 0, 0)
BLUE   = (0, 0, 255)
WHITE  = (255, 255, 255)
YELLOW = (255, 255, 0)
RED    = (255, 0, 0)
GREY   = (150, 150, 150)

# Map Layout (each character is one tile)
# Legend:
# '#' = Wall
# '.' = Pellet
# ' ' = Empty space
# We'll manually place Pac-Man and ghosts, so they're not in the map.
MAP_LAYOUT = [
    "####################",
    "#........##........#",
    "#.##.###..##..###.##",
    "#.##.###..##..###.##",
    "#..................#",
    "#.##.#.######.#.##.#",
    "#....#...##...#....#",
    "####.###.##.###.####",
    "#........##........#",
    "#.##.###..##..###.##",
    "#.##.###..##..###.##",
    "#..................#",
    "#.##.#.######.#.##.#",
    "#....#...##...#....#",
    "####.###.##.###.####",
    "#........##........#",
    "####################"
]

# -----------------------------------------------------------------------------
# Helper Classes & Functions
# -----------------------------------------------------------------------------
class TileType:
    WALL = 0
    PELLET = 1
    EMPTY = 2

def load_map(map_data):
    """
    Convert the textual MAP_LAYOUT into a 2D array of tile types.
    """
    rows = len(map_data)
    cols = len(map_data[0])
    grid = []
    for r in range(rows):
        row_data = []
        for c in range(cols):
            if map_data[r][c] == '#':
                row_data.append(TileType.WALL)
            elif map_data[r][c] == '.':
                row_data.append(TileType.PELLET)
            else:
                row_data.append(TileType.EMPTY)
        grid.append(row_data)
    return grid

def can_move(grid, x, y):
    """
    Check if the tile (x, y) is free to move to (not a wall).
    """
    rows = len(grid)
    cols = len(grid[0])
    if x < 0 or x >= cols or y < 0 or y >= rows:
        return False
    return grid[y][x] != TileType.WALL

def draw_map(screen, grid):
    """
    Draw the walls and pellets on the screen.
    """
    rows = len(grid)
    cols = len(grid[0])
    for r in range(rows):
        for c in range(cols):
            tile = grid[r][c]
            if tile == TileType.WALL:
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, BLUE, rect)
            elif tile == TileType.PELLET:
                center = (c * TILE_SIZE + TILE_SIZE//2, r * TILE_SIZE + TILE_SIZE//2)
                pygame.draw.circle(screen, WHITE, center, 3)

# -----------------------------------------------------------------------------
# Sprite Classes
# -----------------------------------------------------------------------------
class Pacman:
    def __init__(self, x, y):
        self.x = x  # grid-coordinate
        self.y = y
        self.dir_x = 0
        self.dir_y = 0
        self.color = YELLOW
        self.score = 0

    def update(self, grid):
        """
        Move Pacman if the next tile is open.
        """
        new_x = self.x + self.dir_x
        new_y = self.y + self.dir_y
        if can_move(grid, new_x, new_y):
            self.x = new_x
            self.y = new_y
            # If there's a pellet, eat it
            if grid[new_y][new_x] == TileType.PELLET:
                grid[new_y][new_x] = TileType.EMPTY
                self.score += 10

    def draw(self, screen):
        """
        Draw Pac-Man as a circle on the screen.
        """
        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, (px, py), TILE_SIZE // 2 - 2)

class Ghost:
    def __init__(self, x, y, color=RED):
        self.x = x
        self.y = y
        self.color = color
        self.dir_x = 0
        self.dir_y = 0

    def update(self, grid):
        """
        Simple random ghost movement that doesn't move into walls.
        """
        # Attempt to keep moving in the same direction if possible
        if not can_move(grid, self.x + self.dir_x, self.y + self.dir_y):
            # Choose a new direction
            self.dir_x, self.dir_y = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        # Move
        self.x += self.dir_x
        self.y += self.dir_y

    def draw(self, screen):
        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, (px, py), TILE_SIZE // 2 - 2)

# -----------------------------------------------------------------------------
# Main Game Function
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    clock = pygame.time.Clock()

    # Load map
    grid = load_map(MAP_LAYOUT)
    rows = len(grid)
    cols = len(grid[0])

    width = cols * TILE_SIZE
    height = rows * TILE_SIZE

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Pac-Man Demo")

    # Create Pac-Man at a specific tile (e.g., near the center)
    pacman = Pacman(x=1, y=1)

    # Create a few ghosts
    ghosts = [
        Ghost(x=10, y=8, color=RED),
        Ghost(x=10, y=9, color=GREY),
    ]

    # Game loop
    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pacman.dir_x, pacman.dir_y = 0, -1
                elif event.key == pygame.K_DOWN:
                    pacman.dir_x, pacman.dir_y = 0, 1
                elif event.key == pygame.K_LEFT:
                    pacman.dir_x, pacman.dir_y = -1, 0
                elif event.key == pygame.K_RIGHT:
                    pacman.dir_x, pacman.dir_y = 1, 0

        # Update Pac-Man and ghosts
        pacman.update(grid)
        for ghost in ghosts:
            ghost.update(grid)

        # Check collision with ghosts
        for ghost in ghosts:
            if ghost.x == pacman.x and ghost.y == pacman.y:
                # Reset Pac-Man's position
                pacman.x, pacman.y = 1, 1
                pacman.score = 0
                # Optionally, reset pellets or do other game logic
                # For simplicity, we won't reset pellets in this demo.

        # Draw everything
        screen.fill(BLACK)
        draw_map(screen, grid)
        pacman.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        # Display the score in the window title
        pygame.display.set_caption(f"Pac-Man Demo | Score: {pacman.score}")

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
