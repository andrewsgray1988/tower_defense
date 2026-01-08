import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_DIR = "information"

def load_json(file):
    with open(os.path.join(BASE_DIR, JSON_DIR, file)) as json_file:
        return json.load(json_file)

def save_json(file, data):
    full_path = os.path.join(BASE_DIR, JSON_DIR, file)
    with open(full_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)