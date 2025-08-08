from flask import Flask, jsonify
from flask import request
from load_dotenv import load_dotenv
from questdb.ingress import Sender,TimestampNanos
import os
import requests
load_dotenv()

app = Flask(__name__)

url = "http://matrix.sikp.xyz:9000/exec"  # endpoint SQL di QuestDB
auth = (os.environ['DB_USERNAME'], os.environ['DB_PASSWORD'])

@app.route("/")
def hello_world():
    sql = "INSERT INTO prova (test) VALUES ('caricamento da server!')"
    params = {'query': sql}
    response = requests.get(url, params=params, auth=auth)
    if response.status_code == 200:
        print("Inserimento riuscito")
    else:
        print(f"Errore inserimento: {response.status_code} - {response.text}")
    return "<p>Hello, World!</p>"


@app.route('/api/data', methods=['POST'])
def api_data():
    return jsonify({"status":"ok"})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)