import os
import json
import threading

#Sets up the JSON load path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_DIR = "information"

#Loads from the JSON file
def load_json(file):
    with open(os.path.join(BASE_DIR, JSON_DIR, file)) as json_file:
        return json.load(json_file)

#Saves to the JSON file
def save_json(file, data):
    full_path = os.path.join(BASE_DIR, JSON_DIR, file)
    with open(full_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

#Sets up periodic saving for the JSON files
def periodic_save(save_func):
    interval = 30 #Seconds
    save_func() #Save Function
    threading.Timer(interval, periodic_save, args=(save_func, interval)).start()