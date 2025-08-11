import requests
import json

class APIClient:
    def __init__(self, base_url="http://localhost:9009"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session() 
        self.session.headers.update({"Content-Type": "application/json"})
        print(f"Client inizializzato per il server: {self.base_url}")

    def _make_request(self, method, endpoint, data=None):
        """Funzione helper per eseguire le richieste e gestire le risposte."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, data=json.dumps(data) if data else None)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Errore HTTP: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Errore di connessione: {e}")
        except json.JSONDecodeError:
            print("Errore: La risposta non è un JSON valido.")
        return None

    def register(self, username, password):
        print(f"\n[TEST] Tentativo di registrare l'utente '{username}'...")
        payload = {"username": username, "password": password}
        response = self._make_request("POST", "/api/user/register", data=payload)
        if response:
            print(f"Risposta dal server: {response}")
        return response

    def login(self, username, password):
        print(f"\n[TEST] Tentativo di login per l'utente '{username}'...")
        payload = {"username": username, "password": password}
        response = self._make_request("POST", "/api/user/login", data=payload)
        if response and response.get("status") == 0:
            self.token = response.get("data", {}).get("token")
            if self.token:
                print(f"Login riuscito! Token ricevuto: {self.token[:10]}...")
                # Aggiorna l'header per le richieste future
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            else:
                 print("Login riuscito, ma nessun token ricevuto.")
        elif response:
             print(f"Login fallito: {response.get('message')}")
        return response

    def get_my_info(self):
        print("\n[TEST] Tentativo di accedere all'endpoint protetto /api/get_my_info...")
        if not self.token:
            print("Azione fallita: nessun token di sessione. Esegui prima il login.")
        
        response = self._make_request("GET", "/api/get_my_info")
        if response:
            print(f"Risposta dal server: {response}")
        return response

if __name__ == "__main__":
    client = APIClient()
    
    client.register("test_user_1", "password123")
    
    client.register("test_user_1", "password123")

    client.get_my_info()

    client.login("test_user_1", "wrong_password")

    client.login("test_user_1", "password123")

    client.get_my_info()
    
    old_token = client.token
    client.login("test_user_1", "password123")
    new_token = client.token

    print(f"\nVecchio token: {old_token[:10]}...")
    print(f"Nuovo token:   {new_token[:10]}...")
    print(f"I token sono diversi? {old_token != new_token}")

    print("\n[TEST] Tentativo di usare il vecchio token invalidato...")
    client.session.headers.update({"Authorization": f"Bearer {old_token}"})
    client.get_my_info()

    # 9. Ripristina il token corretto e verifica che funzioni ancora
    print("\n[TEST] Ripristino il token valido e riprovo...")
    client.session.headers.update({"Authorization": f"Bearer {new_token}"})
    client.get_my_info()