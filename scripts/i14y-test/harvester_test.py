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

def load_data(file_path: str) -> Dict[str, Any]:
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading data from {file_path}: {e}")
    return {}

def save_data(data: Dict[str, Any], file_path: str) -> None:
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file)
    except IOError as e:
        print(f"Error saving data to {file_path}: {e}")

def compare_and_update_data(get_endpoint: str, post_endpoint: str, get_token: str, post_token: str, file_path: str) -> None:
    try:
        data = get_data(get_endpoint, get_token)
        previous_data = load_data(file_path)
        
        # For first run or if data has changed
        if not previous_data or data != previous_data:
            # Add version timestamp
            now = datetime.now()
            timestamp = now.strftime("%Y.%m.%d%H%M")
            data['data']['version'] = timestamp
            
            # Save the updated data
            save_data(data, file_path)
            
            # Post the new version
            post_data(post_endpoint, json.dumps(data), post_token)
            print(f"Data updated and posted successfully at {timestamp}")
        else:
            print("No changes detected in data")
            
    except Exception as e:
        print(f"Error in compare_and_update_data: {e}")
        raise


if __name__ == "__main__":

    # Get repository root directory (harvester/script)
    workspace = os.getcwd()
    path_to_data = os.path.join(workspace, 'i14y-test', 'data', 'data.json')
    
    print(f"Current working directory: {workspace}")
    print(f"Data file path: {path_to_data}")
    
    # get the data from the harvested endpoint and post any changes
    compare_and_update_data(
        GET_ENDPOINT_FROM,
        POST_ENDPOINT,
        ACCESS_TOKEN,
        ACCESS_TOKEN,
        path_to_data
    )
    
    try:
        log = f"Harvest completed successfully at {datetime.now()}\n"
    except Exception as e:
        log = f"Harvest failed at {datetime.now()}: {str(e)}\n"
        raise
    finally:
        # Save log in root directory
        with open('harvest_log.txt', 'w') as f:
            f.write(log)
