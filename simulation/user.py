import uuid
import requests
import json
import random
import math

class User:
    def __init__(self, username, password, base_url, x, y, size, aura, width, height, max_sleep_time, max_receive_time, max_beacon_time):
        self.states = {
            "SLEEP" : 0,
            "IDLE" : 1,
            "BEACON" : 2,
            "RECEIVE" : 3
        }

        self.max_sleep_time = max_sleep_time
        self.max_receive_time = max_receive_time
        self.max_beacon_time = max_beacon_time
        self.uuid = str(uuid.uuid4())
        self.username = username
        self.password = password
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

        self.direction_change_timer = 0
        self.direction_change_interval = random.randint(60, 180)

        self.target_x = x
        self.target_y = y

        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 0.005
        self.max_speed = 0.1
        self.acceleration = 0.01

        self.device_found = set()

        # State Machine Timers
        self.set_state_timer()
    
        self.start_time = 0

        self.state = random.randint(0,3)

    def set_state_timer(self):
        self.sleep_time = random.randint(1,self.max_sleep_time)
        self.beacon_time = random.randint(1,self.max_beacon_time)
        self.receive_time = random.randint(1, self.max_receive_time)
        self.idle_time = 1
    
    def change_state(self, deltatime):
        elapsed_time = deltatime - self.start_time

        if self.state == 0 and elapsed_time >= self.sleep_time:
            #From sleep to beacon
            self.state = self.states["BEACON"]
            self.start_time = deltatime
        elif self.state == 1 and elapsed_time >= self.idle_time:
            #From idle to sleep
            self.state = self.states["SLEEP"]
            self.start_time = deltatime
            self.set_state_timer()
        elif self.state == 2 and elapsed_time >= self.beacon_time:
            #From beacon to receive
            self.state = self.states["RECEIVE"]
            self.start_time = deltatime
        elif self.state == 3 and elapsed_time >= self.receive_time:
            #From receive to idle
            self.state = self.states["IDLE"]
            self.start_time = deltatime
            if len(self.device_found) > 0:
                self.send_data_to_server()
            self.device_found = set()
        
    def send_data_to_server(self):
        for device in self.device_found:
            payload = {"user": self.uuid, "match": device}
            response = self._make_request("POST", "/api/post_connection", data=payload)


    def choose_new_target(self):
        margin = 10  # Margine dai bordi
        self.target_x = random.randint(margin, self.max_width - margin)
        self.target_y = random.randint(margin, self.max_height - margin)

    def move_with_inertia(self):
        """Movimento più naturale con inerzia"""
        # Cambia direzione periodicamente
        self.direction_change_timer += 1
        if self.direction_change_timer >= self.direction_change_interval:
            self.choose_new_target()
            self.direction_change_timer = 0
            self.direction_change_interval = random.randint(60, 180)
        
        # Calcola direzione verso il target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 1:
            # Normalizza la direzione
            target_vel_x = (dx / distance) * self.max_speed
            target_vel_y = (dy / distance) * self.max_speed
        else:
            target_vel_x = 0
            target_vel_y = 0
        
        # Applica accelerazione verso la velocità target
        self.velocity_x += (target_vel_x - self.velocity_x) * self.acceleration
        self.velocity_y += (target_vel_y - self.velocity_y) * self.acceleration
        
        # Aggiungi rumore per movimento più naturale
        self.velocity_x += (random.random() - 0.5) * 0.1
        self.velocity_y += (random.random() - 0.5) * 0.1
        
        # Limita velocità massima
        vel_magnitude = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if vel_magnitude > self.max_speed:
            self.velocity_x = (self.velocity_x / vel_magnitude) * self.max_speed
            self.velocity_y = (self.velocity_y / vel_magnitude) * self.max_speed
        
        # Calcola nuova posizione
        new_x = self.x + self.velocity_x
        new_y = self.y + self.velocity_y
        
        # Gestisci i bordi con rimbalzo
        if new_x <= self.radius or new_x >= self.max_width - self.radius:
            self.velocity_x *= -0.8  # Rimbalza con un po' di perdita di energia
            new_x = max(self.radius, min(self.max_width - self.radius, new_x))
            self.choose_new_target()  # Cambia direzione quando colpisce un bordo
            
        if new_y <= self.radius or new_y >= self.max_height - self.radius:
            self.velocity_y *= -0.8
            new_y = max(self.radius, min(self.max_height - self.radius, new_y))
            self.choose_new_target()
            
        self.x = new_x
        self.y = new_y




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

        response = self.session.request(method, url, data=json.dumps(data) if data else None)
        #response.raise_for_status()
        return response.json()
    

    def compute_distance(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def check_collisions(self, users):
        # Do not check for collision if i'm not transmitting
        if self.state != 2:
            return
        for user in users:
            if user.uuid == self.uuid:
                # Confronting with myself
                continue
            distance = self.compute_distance(user)
            if distance+self.radius < self.aura:
                # The other user is listening
                if user.state == 3:
                    user.device_found.add(self.uuid)
            

