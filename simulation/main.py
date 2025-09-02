import pygame
import random
from user import User

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RECEIVE_COLOR = (0, 255, 0)
BEACON_COLOR = (255, 0, 0)
SLEEP_COLOR = (100, 100, 255)
IDLE_COLOR = (100, 100, 100)

WIDTH, HEIGHT = 800, 600
N_USERS = 60
N_GROUPS = 8
SIZE = 5
AURA = 35
PERC_FAIL = 0.90


MAX_SLEEP_TIME = 30
MAX_RECEIVE_TIME = 15
MAX_BEACON_TIME = 5

POINTS_OF_INTEREST = [
    {"name": "Bar", "pos": (70, 70), "radius": 50, "color": (255, 255, 0)},
    {"name": "Stage", "pos": (WIDTH // 2, HEIGHT - 50), "radius": 80, "color": (255, 0, 255)},
    {"name": "Relax Area", "pos": (WIDTH - 80, 80), "radius": 60, "color": (0, 255, 255)},
]

def create_groups(users_list, num_groups):
    random.shuffle(users_list)
    groups = [[] for _ in range(num_groups)]
    for i, user in enumerate(users_list):
        groups[i % num_groups].append(user)
    return groups

def main():
    pygame.init()
    canvas = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ProximityNet")
    
    aura_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    clock = pygame.time.Clock()

    users_credentials = []
    users = []
    
    for i in range(N_USERS):
        users_credentials.append((f"username_{i}", f"password_{i}"))
    
    for user_credential in users_credentials:
        x = random.randrange(10, WIDTH-10)
        y = random.randrange(10, HEIGHT-10)
        user = User(
            user_credential[0],
            user_credential[1],
            "http://5.196.14.6:9010",
            x, y, SIZE, AURA, WIDTH, HEIGHT,
            MAX_SLEEP_TIME, MAX_RECEIVE_TIME, MAX_BEACON_TIME, PERC_FAIL
        )
        if user.is_logged:
            users.append(user)
        else:
            raise Exception("Error logging user ", user_credential)

    user_groups = create_groups(users, N_GROUPS)
    group_info = {}
    for i, group in enumerate(user_groups):
        center_x = sum(u.x for u in group) / len(group)
        center_y = sum(u.y for u in group) / len(group)
        
        group_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

        group_info[i] = {
            "center": pygame.Vector2(center_x, center_y),
            "target": pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT)),
            "color": group_color 
        }
        for user in group:
            user.assign_group_and_color(i, group_color)

    elapsed_time = 0.0
    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        elapsed_time += delta_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        for i in group_info:
            info = group_info[i]
            info["center"].move_towards_ip(info["target"], 0.1)
            if info["center"].distance_to(info["target"]) < 20:
                info["target"] = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))

        for user in users:
            group_center = group_info[user.group_id]["center"]
            user.update_behavior(delta_time, group_center, POINTS_OF_INTEREST)
            user.change_state(elapsed_time)

        for user in users:
            user.check_collisions(users)
        
        canvas.fill(WHITE)
        aura_surface.fill((0, 0, 0, 0))

        for poi in POINTS_OF_INTEREST:
            pygame.draw.circle(canvas, poi["color"], poi["pos"], poi["radius"], 2)

        for user in users:
            state_colors = {0: SLEEP_COLOR, 1: IDLE_COLOR, 2: BEACON_COLOR, 3: RECEIVE_COLOR}
            aura_color = (*state_colors.get(user.state, IDLE_COLOR), 50)
            pygame.draw.circle(aura_surface, aura_color, (user.x, user.y), user.aura)
        
        canvas.blit(aura_surface, (0, 0))
        
        for user in users:
            pygame.draw.circle(canvas, user.color, (user.x, user.y), user.radius)
        
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()