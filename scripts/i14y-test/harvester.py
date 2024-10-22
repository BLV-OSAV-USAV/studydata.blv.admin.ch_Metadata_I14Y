import requests
import json
import os
from typing import Dict, Any

from datetime import datetime

GET_ENDPOINT_FROM = os.environ['GET_ENDPOINT_FROM']
GET_ENDPOINT_TO = os.environ['GET_ENDPOINT_TO']
POST_ENDPOINT = os.environ['POST_ENDPOINT']
ACCESS_TOKEN = f"Bearer {os.environ['ACCESS_TOKEN']}" 

def get_data(endpoint, token):
    response = requests.get(url=endpoint, headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': 'application/+json', 'Accept-encoding': 'json'}, verify=False)
    response.raise_for_status()
    return response.json()

def post_data(endpoint, data, token):
    response = requests.post(endpoint, data=data, headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, verify=False)
    response.raise_for_status()
    return response.json()

def load_data(file_path:str) -> Dict[str, Any]:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_data(data: Dict[str, Any], file_path:str) -> None:
    with open(file_path, 'w') as file:
        json.dump(data, file)

def compare_and_update_data(get_endpoint: str, post_endpoint: str, get_token: str, post_token: str, file_path: str) -> None:
        data = get_data(get_endpoint, get_token)
        previous_data = load_data(file_path)
        # check any changes since yesterday
        if data != previous_data:
            save_data(data,file_path)
            # post a new version of the data - to be replaced by a mapping function and a put request
            now = datetime.now()
            timestamp = now.strftime("%Y.%m.%d%H%M")
            data['data']['version'] = timestamp
            data = json.dumps(data)
            post_data(post_endpoint, data, post_token)


if __name__ == "__main__":

    workspace = os.getcwd()
    path_to_data = os.path.join(workspace, 'downloaded-data', 'i14y-test/data/data.json')
        
    # get the data from the harvested endpoint and post any changes
    compare_and_update_data(GET_ENDPOINT_FROM, POST_ENDPOINT, ACCESS_TOKEN, ACCESS_TOKEN, path_to_data)

    # Generate log and save to file
    log = f"Harvest completed at {datetime.now()}\n"
    with open('harvest_log.txt', 'w') as f:
        f.write(log)
