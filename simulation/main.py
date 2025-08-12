from user import User
import pygame
import random
import time

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RECEIVE_COLOR = (0, 255, 0)
BEACON_COLOR = (255, 0, 0)
SLEEP_COLOR = (100, 100, 255)  # Colore blu per l'aura
IDLE_COLOR = (100, 100, 100)  # Colore blu per l'aura

MAX_SLEEP_TIME = 30
MAX_RECEIVE_TIME = 15
MAX_BEACON_TIME = 5

WIDTH = 500
HEIGHT = 500
N_USERS = 30
SIZE = 5
AURA = 35

def main():
    canvas = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ProximityNet")
    exit = False
    users_credentials = []
    users = []
    
    # Crea una superficie per le aure con supporto alpha
    aura_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    clock = pygame.time.Clock()
    
    for i in range(N_USERS):
        users_credentials.append(
            (f"username_{i}", f"password_{i}")
        )
    
    for user_credential in users_credentials:
        x = random.randrange(10, WIDTH-10)
        y = random.randrange(10, HEIGHT-10)
        user = User(user_credential[0],
                    user_credential[1],
                    "http://localhost:9009",
                    x,
                    y,
                    SIZE,
                    AURA,
                    WIDTH,
                    HEIGHT,
                    MAX_SLEEP_TIME,
                    MAX_RECEIVE_TIME,
                    MAX_BEACON_TIME
                )
        if user.is_logged:
            users.append(user)
        else:
            raise Exception("Error logging user ", user_credential)
    # Start the simulation loop
    elapsed_time = 0.0
    while not exit:
        delta_time = clock.tick(60) / 1000.0  # Secondi tra frame
        elapsed_time+=delta_time
        # 1: move the users
        for user in users:
            user.move_with_inertia()
        
        # 2: Update state
        for user in users:
            user.change_state(elapsed_time)

        canvas.fill(WHITE)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
        
        # Pulisci la superficie dell'aura
        aura_surface.fill((0, 0, 0, 0))  # Trasparente
        
        # Disegna le aure sulla superficie trasparente
        for user in users:
            # Il quarto valore (50) è l'opacità: 0=trasparente, 255=opaco
            
            if user.state == 0:
                aura_color = SLEEP_COLOR
            elif user.state == 1:
                aura_color = IDLE_COLOR
            elif user.state == 2:
                aura_color = BEACON_COLOR
            elif user.state == 3:
                aura_color = RECEIVE_COLOR


            aura_color_with_alpha = (*aura_color, 50)
            pygame.draw.circle(aura_surface, aura_color_with_alpha, (user.x, user.y), user.aura)
        
        # Applica la superficie delle aure al canvas principale
        canvas.blit(aura_surface, (0, 0))
        
        # Disegna gli utenti sopra le aure
        for user in users:
            pygame.draw.circle(canvas, BLACK, (user.x, user.y), user.radius)
        
        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    main()