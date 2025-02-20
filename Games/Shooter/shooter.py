import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter Game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Player settings
player_size = 50
player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2 * player_size]
player_speed = 10

# Enemy settings
enemy_size = 50
enemy_pos = [random.randint(0, SCREEN_WIDTH - enemy_size), 0]
enemy_list = [enemy_pos]
enemy_speed = 7

# Bullet settings
bullet_size = 10
bullet_pos = []
bullet_list = []

# Clock for controlling the frame rate
clock = pygame.time.Clock()

# Score
score = 0

def drop_enemies(enemy_list):
    delay = random.random()
    if len(enemy_list) < 10 and delay < 0.1:
        x_pos = random.randint(0, SCREEN_WIDTH - enemy_size)
        y_pos = 0
        enemy_list.append([x_pos, y_pos])

def draw_enemies(enemy_list):
    for enemy_pos in enemy_list:
        pygame.draw.rect(screen, RED, (enemy_pos[0], enemy_pos[1], enemy_size, enemy_size))

def update_enemy_positions(enemy_list, score):
    for idx, enemy_pos in enumerate(enemy_list):
        if enemy_pos[1] >= 0 and enemy_pos[1] < SCREEN_HEIGHT:
            enemy_pos[1] += enemy_speed
        else:
            enemy_list.pop(idx)
            score += 1
    return score

def draw_bullets(bullet_list):
    for bullet_pos in bullet_list:
        pygame.draw.rect(screen, WHITE, (bullet_pos[0], bullet_pos[1], bullet_size, bullet_size))

def update_bullet_positions(bullet_list):
    for idx, bullet_pos in enumerate(bullet_list):
        if bullet_pos[1] > 0:
            bullet_pos[1] -= 5
        else:
            bullet_list.pop(idx)

def collision_check(enemy_list, bullet_list):
    for enemy_pos in enemy_list[:]:
        for bullet_pos in bullet_list[:]:
            if detect_collision(enemy_pos, bullet_pos):
                enemy_list.remove(enemy_pos)
                bullet_list.remove(bullet_pos)
                return True
    return False

def detect_collision(player_pos, enemy_pos):
    p_x = player_pos[0]
    p_y = player_pos[1]

    e_x = enemy_pos[0]
    e_y = enemy_pos[1]

    if (e_x >= p_x and e_x < (p_x + player_size)) or (p_x >= e_x and p_x < (e_x + enemy_size)):
        if (e_y >= p_y and e_y < (p_y + player_size)) or (p_y >= e_y and p_y < (e_y + enemy_size)):
            return True
    return False

def game_over():
    font = pygame.font.SysFont("monospace", 35)
    label = font.render(f"Game Over! Your score is {score}", 1, RED)
    screen.blit(label, (SCREEN_WIDTH // 4 - 20, SCREEN_HEIGHT // 3))
    pygame.display.update()
    time.sleep(2)
    pygame.quit()
    exit()

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            x = player_pos[0]
            y = player_pos[1]

            if event.key == pygame.K_LEFT and x > 0:
                x -= player_speed
            elif event.key == pygame.K_RIGHT and x < SCREEN_WIDTH - player_size:
                x += player_speed
            elif event.key == pygame.K_SPACE:
                bullet_pos = [x + player_size // 2, y]
                bullet_list.append(bullet_pos)

            player_pos = [x, y]

    screen.fill((0, 0, 0))

    drop_enemies(enemy_list)
    score = update_enemy_positions(enemy_list, score)
    draw_enemies(enemy_list)

    update_bullet_positions(bullet_list)
    draw_bullets(bullet_list)

    if collision_check(enemy_list, bullet_list):
        game_over()

    pygame.draw.rect(screen, WHITE, (player_pos[0], player_pos[1], player_size, player_size))

    clock.tick(30)
    pygame.display.update()