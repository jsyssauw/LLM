import tkinter as tk
import random
import winsound  # <-- Only works reliably on Windows

# -----------------------------------------------------------------------------
# Game Constants
# -----------------------------------------------------------------------------
TILE_SIZE = 24
UPDATE_DELAY = 100  # milliseconds (~10 FPS)

# Beep settings (for Windows)
PELLET_BEEP_FREQ    = 600  # Hz
PELLET_BEEP_DURATION= 50   # ms
GHOST_BEEP_FREQ     = 200  # Hz
GHOST_BEEP_DURATION = 150  # ms

COLOR_WALL   = "blue"
COLOR_PELLET = "white"
COLOR_BG     = "black"
COLOR_PACMAN = "yellow"
COLOR_GHOST  = "red"
COLOR_GHOST2 = "grey"

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
    WALL   = 0
    PELLET = 1
    EMPTY  = 2

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
            char = map_data[r][c]
            if char == '#':
                row_data.append(TileType.WALL)
            elif char == '.':
                row_data.append(TileType.PELLET)
            else:
                row_data.append(TileType.EMPTY)
        grid.append(row_data)
    return grid

def can_move(grid, x, y):
    """
    Check if the tile (x, y) is free (not a wall).
    """
    rows = len(grid)
    cols = len(grid[0])
    if x < 0 or x >= cols or y < 0 or y >= rows:
        return False
    return grid[y][x] != TileType.WALL

# -----------------------------------------------------------------------------
# Sound (Windows-only) Helper Functions
# -----------------------------------------------------------------------------
def beep_eat_pellet():
    """
    Beep when Pac-Man eats a pellet.
    """
    winsound.Beep(PELLET_BEEP_FREQ, PELLET_BEEP_DURATION)

def beep_ghost_collision():
    """
    Beep when Pac-Man collides with a ghost.
    """
    winsound.Beep(GHOST_BEEP_FREQ, GHOST_BEEP_DURATION)

# -----------------------------------------------------------------------------
# Game Entities
# -----------------------------------------------------------------------------
class Pacman:
    def __init__(self, x, y, canvas, grid):
        self.x = x
        self.y = y
        self.dir_x = 0
        self.dir_y = 0
        self.score = 0

        self.canvas = canvas
        self.grid = grid

        px = x * TILE_SIZE + TILE_SIZE // 2
        py = y * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 2
        self.canvas_item = canvas.create_oval(
            px - radius, py - radius,
            px + radius, py + radius,
            fill=COLOR_PACMAN, outline=""
        )

    def set_direction(self, dx, dy):
        self.dir_x = dx
        self.dir_y = dy

    def update(self):
        new_x = self.x + self.dir_x
        new_y = self.y + self.dir_y
        if can_move(self.grid, new_x, new_y):
            self.x = new_x
            self.y = new_y
            # Eat pellet if present
            if self.grid[new_y][new_x] == TileType.PELLET:
                self.grid[new_y][new_x] = TileType.EMPTY
                self.score += 10
                # Play pellet beep
                beep_eat_pellet()

        # Move the canvas item to the new position
        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        self.canvas.coords(self.canvas_item,
            px - (TILE_SIZE // 2 - 2), py - (TILE_SIZE // 2 - 2),
            px + (TILE_SIZE // 2 - 2), py + (TILE_SIZE // 2 - 2))

class Ghost:
    def __init__(self, x, y, canvas, grid, color=COLOR_GHOST):
        self.x = x
        self.y = y
        self.dir_x = 0
        self.dir_y = 0
        self.canvas = canvas
        self.grid = grid

        px = x * TILE_SIZE + TILE_SIZE // 2
        py = y * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 2
        self.canvas_item = canvas.create_oval(
            px - radius, py - radius,
            px + radius, py + radius,
            fill=color, outline=""
        )

        # Start in a random direction
        self._choose_random_direction()

    def _choose_random_direction(self):
        self.dir_x, self.dir_y = random.choice([(1,0), (-1,0), (0,1), (0,-1)])

    def update(self):
        new_x = self.x + self.dir_x
        new_y = self.y + self.dir_y
        if not can_move(self.grid, new_x, new_y):
            self._choose_random_direction()
        else:
            self.x = new_x
            self.y = new_y

        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        self.canvas.coords(self.canvas_item,
            px - (TILE_SIZE // 2 - 2), py - (TILE_SIZE // 2 - 2),
            px + (TILE_SIZE // 2 - 2), py + (TILE_SIZE // 2 - 2))

# -----------------------------------------------------------------------------
# Main Game Class
# -----------------------------------------------------------------------------
class PacmanGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pac-Man Demo (Tkinter)")

        # Load map & grid
        self.grid_data = load_map(MAP_LAYOUT)
        self.rows = len(self.grid_data)
        self.cols = len(self.grid_data[0])

        width = self.cols * TILE_SIZE
        height = self.rows * TILE_SIZE

        self.canvas = tk.Canvas(self, width=width, height=height, bg=COLOR_BG)
        self.canvas.pack()

        self.draw_map()

        # Create Pac-Man
        self.pacman = Pacman(x=1, y=1, canvas=self.canvas, grid=self.grid_data)

        # Create ghosts
        self.ghosts = [
            Ghost(x=10, y=8,  canvas=self.canvas, grid=self.grid_data, color=COLOR_GHOST),
            Ghost(x=10, y=9,  canvas=self.canvas, grid=self.grid_data, color=COLOR_GHOST2),
        ]

        # Bind arrow keys
        self.bind("<Up>",    lambda e: self.pacman.set_direction(0, -1))
        self.bind("<Down>",  lambda e: self.pacman.set_direction(0,  1))
        self.bind("<Left>",  lambda e: self.pacman.set_direction(-1, 0))
        self.bind("<Right>", lambda e: self.pacman.set_direction(1,  0))

        # Start the update loop
        self.update_game()

    def draw_map(self):
        """
        Draw walls (blue rectangles) & pellets (small white circles).
        """
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid_data[r][c]
                x1 = c * TILE_SIZE
                y1 = r * TILE_SIZE
                x2 = x1 + TILE_SIZE
                y2 = y1 + TILE_SIZE

                if tile == TileType.WALL:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=COLOR_WALL, outline=""
                    )
                elif tile == TileType.PELLET:
                    cx = x1 + TILE_SIZE // 2
                    cy = y1 + TILE_SIZE // 2
                    r_p = 3
                    self.canvas.create_oval(
                        cx - r_p, cy - r_p,
                        cx + r_p, cy + r_p,
                        fill=COLOR_PELLET, outline=""
                    )

    def update_game(self):
        """
        Main game loop: update Pac-Man, update ghosts, check collisions,
        schedule next update.
        """
        # Update Pac-Man
        self.pacman.update()

        # Update ghosts
        for ghost in self.ghosts:
            ghost.update()

        # Check collision with ghosts
        for ghost in self.ghosts:
            if ghost.x == self.pacman.x and ghost.y == self.pacman.y:
                # Play a beep for collision
                beep_ghost_collision()

                # Reset Pac-Man
                self.pacman.x, self.pacman.y = 1, 1
                self.pacman.score = 0
                # Optionally reset the map or ghost positions, etc.

        # Update window title
        self.title(f"Pac-Man Demo (Tkinter) | Score: {self.pacman.score}")

        # Schedule next frame
        self.after(UPDATE_DELAY, self.update_game)

def main():
    game = PacmanGame()
    game.mainloop()

if __name__ == "__main__":
    main()
