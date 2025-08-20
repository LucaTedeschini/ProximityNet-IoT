# user.py (Fedele all'originale per la parte di rete)

import uuid
import requests
import json
import random
import math
import pygame # Aggiungiamo pygame per usare i vettori

class User:
    # --- __INIT__ RIPRISTINATO ALL'ORIGINALE + AGGIUNTE PER NUOVA LOGICA ---
    def __init__(self, username, password, base_url, x, y, size, aura, width, height, max_sleep_time, max_receive_time, max_beacon_time, perc_fail):
        # La parte di inizializzazione è identica all'originale
        self.states = {"SLEEP" : 0, "IDLE" : 1, "BEACON" : 2, "RECEIVE" : 3}
        self.max_sleep_time = max_sleep_time
        self.max_receive_time = max_receive_time
        self.max_beacon_time = max_beacon_time
        self.uuid = str(uuid.uuid4())
        self.username = username
        self.password = password
        self.perc_fail = perc_fail
        self.base_url = base_url
        self.session = requests.Session() 
        self.session.headers.update({"Content-Type": "application/json"})
        self.is_logged = False
        self.login(username, password)
        self.x = x
        self.y = y
        self.max_width = width - 30
        self.max_height = height - 30
        self.radius=size
        self.aura = aura
        self.device_found = set()
        self.set_state_timer()
        self.start_time = 0
        self.state = random.randint(0,3)
        # Ho rimosso la vecchia logica di movimento casuale per sostituirla

        # --- NUOVA AGGIUNTA: Logica di movimento basata su obiettivi ---
        self.pos = pygame.Vector2(x, y) # Usiamo i vettori per una fisica più semplice
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = random.uniform(0.2, 0.4)
        self.acceleration = 0.01
        self.group_id = -1
        self.movement_mode = "GROUPING"
        self.current_target = self.pos
        self.decision_timer = 0
        self.decision_interval = random.uniform(5, 15)
        self.color = (0, 0, 0)

    # --- NUOVA AGGIUNTA: Metodi per il comportamento sociale ---
    def assign_group(self, group_id):
        self.group_id = group_id

    def assign_group_and_color(self, group_id, color):
        """Assegna l'ID del gruppo e il colore del gruppo all'utente."""
        self.group_id = group_id
        self.color = color

    def decide_next_move(self, group_center, points_of_interest):
        self.decision_timer = 0
        self.decision_interval = random.uniform(20, 30)
        self.movement_mode = random.choices(["GROUPING", "HOTSPOT", "WANDERING"], weights=[0.70, 0.28, 0.02], k=1)[0]
        
        if self.movement_mode == "GROUPING":
            self.current_target = group_center + pygame.Vector2(random.uniform(-15, 15), random.uniform(-15, 15))
        elif self.movement_mode == "HOTSPOT":
            poi = random.choice(points_of_interest)
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, poi["radius"])
            self.current_target = pygame.Vector2(poi["pos"]) + pygame.Vector2(math.cos(angle) * radius, math.sin(angle) * radius)
        else: # WANDERING
            self.current_target = pygame.Vector2(random.uniform(0, self.max_width), random.uniform(0, self.max_height))

    def update_behavior(self, delta_time, group_center, points_of_interest):
        """Questa funzione ora gestisce SOLO il movimento, sostituendo move_with_inertia."""
        self.decision_timer += delta_time
        if self.decision_timer > self.decision_interval:
            self.decide_next_move(group_center, points_of_interest)

        direction_to_target = self.current_target - self.pos
        if direction_to_target.length() > 1:
            desired_velocity = direction_to_target.normalize() * self.max_speed
            self.velocity.move_towards_ip(desired_velocity, self.acceleration * 100)
        else:
            self.velocity.move_towards_ip(pygame.Vector2(0,0), self.acceleration * 100)

        self.pos += self.velocity
        
        if not (self.radius < self.pos.x < self.max_width - self.radius):
            self.velocity.x *= -0.5
            self.pos.x = max(self.radius, min(self.pos.x, self.max_width - self.radius))
        if not (self.radius < self.pos.y < self.max_height - self.radius):
            self.velocity.y *= -0.5
            self.pos.y = max(self.radius, min(self.pos.y, self.max_height - self.radius))
            
        # Aggiorna le coordinate x, y originali per compatibilità con il resto del codice
        self.x = self.pos.x
        self.y = self.pos.y

    # --- TUTTE LE FUNZIONI SEGUENTI SONO IDENTICHE ALL'ORIGINALE ---

    def set_state_timer(self):
        self.sleep_time = random.randint(1,self.max_sleep_time)
        self.beacon_time = random.randint(1,self.max_beacon_time)
        self.receive_time = random.randint(1, self.max_receive_time)
        self.idle_time = 1
    
    def change_state(self, deltatime):
        elapsed_time = deltatime - self.start_time
        if self.state == 0 and elapsed_time >= self.sleep_time:
            self.state = self.states["BEACON"]; self.start_time = deltatime
        elif self.state == 1 and elapsed_time >= self.idle_time:
            self.state = self.states["SLEEP"]; self.start_time = deltatime; self.set_state_timer()
        elif self.state == 2 and elapsed_time >= self.beacon_time:
            self.state = self.states["RECEIVE"]; self.start_time = deltatime
        elif self.state == 3 and elapsed_time >= self.receive_time:
            self.state = self.states["IDLE"]; self.start_time = deltatime
            if len(self.device_found) > 0: self.send_data_to_server()
            self.device_found = set()
        
    def send_data_to_server(self):
        for device in self.device_found:
            chance = random.random()
            if chance >= self.perc_fail:
                payload = {"user": self.uuid, "match": device}
                response = self._make_request("POST", "/api/post_connection", data=payload)

    def register(self, username, password):
        payload = {"username": username, "password": password}
        self._make_request("POST", "/api/user/register", data=payload)

    def login(self, username, password):
        payload = {"username": username, "password": password}
        response = self._make_request("POST", "/api/user/login", data=payload)
        if response and response.get("status") == 0:
            self.token = response.get("data", {}).get("token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.is_logged=True
                return
        elif response and response.get("status") == 1:
            self.register(username, password)
            self.login(username, password)
        else:
            self.is_logged=False
            return 
        
    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, data=json.dumps(data) if data else None, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # print(f"Errore di rete ({e}), restituisco risposta fittizia.")
            return {"status": 1, "message": "Network error"}

    def compute_distance(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def check_collisions(self, users):
        if self.state != 2: return
        for user in users:
            if user.uuid == self.uuid: continue
            distance = self.compute_distance(user)
            if distance + self.radius < self.aura:
                if user.state == 3:
                    user.device_found.add(self.uuid)