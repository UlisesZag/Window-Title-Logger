import json
import os

#Cargar config
def load_config(path):
    if not os.path.exists(path):
        save_config(path, {
            "log_time_interval": 1,
            "wait_time_interval": 0.25
        })
    
    with open(path, "r") as file:
        json_config = file.read()
        config = json.loads(json_config)
    
    return config

#Guardar config
def save_config(path,config):
    with open(path, "w") as file:
        file.write(json.dumps(config))