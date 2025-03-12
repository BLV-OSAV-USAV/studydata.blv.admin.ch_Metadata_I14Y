import requests
import json
import os
import urllib3
import datetime
from dateutil import parser
from typing import Dict, Any
from mapping import map_dataset

GET_ENDPOINT_FROM_UNISANTE = os.environ['GET_ENDPOINT_FROM_UNISANTE']
PUT_ENDPOINT_TO_I14Y = os.environ['PUT_ENDPOINT_TO_I14Y']
POST_ENDPOINT_TO_I14Y = os.environ['POST_ENDPOINT_TO_I14Y']
IDS_I14Y = json.loads(os.environ['IDS_I14Y'])
ACCESS_TOKEN = f"Bearer {os.environ['ACCESS_TOKEN']}" 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def put_data_to_i14y(id, data, token):
    response = requests.put(
        url = PUT_ENDPOINT_TO_I14Y + id,
        data=data, 
        headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
        verify=False
    )
    response.raise_for_status()
    return response.json()


def post_data_to_i14y(data, token):
    response = requests.post(
        url = POST_ENDPOINT_TO_I14Y,
        data=data, 
        headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
        verify=False
    )
    response.raise_for_status()
    return response.json()


def change_level_i14y(id, level, token):
    response = requests.put(
            url = PUT_ENDPOINT_TO_I14Y + id + '/publication-level',
            params = {'level': level}, 
            headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
            verify=False
        )
    response.raise_for_status()
    return response.json()

def change_status_i14y(id, status, token):
    response = requests.put(
            url = PUT_ENDPOINT_TO_I14Y + id + '/registration-status',
            params = {'status': status}, 
            headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
            verify=False
        )
    response.raise_for_status()
    return response.json()
    
def save_data(data: Dict[str, Any], file_path: str) -> None:
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file)
    except IOError as e:
        print(f"Error saving data to {file_path}: {e}")


if __name__ == "__main__":

  # Get repository root directory (harvester/script) and previous saved catalogue data
    workspace = os.getcwd()
    path_to_data = os.path.join(workspace, 'unisante', 'data', 'I14Y_IDS.json')
    try: 
        with open(path_to_data, 'r') as f:
            previous_I14Y_IDS = json.load(f)
            print("Successfully loaded previous data")
    except FileNotFoundError:
            previous_I14Y_IDS = IDS_I14Y
            print("Using initial data")
    
    s = requests.Session()

  # Get catalogue 
    response = s.get(url = GET_ENDPOINT_FROM_UNISANTE + 'search', verify=False, timeout=40.0)
    catalog = response.json()

  # Get yesterday's date in UTC+1
    utc_plus_1 = datetime.timezone(datetime.timedelta(hours=1))
    now_utc_plus_1 = datetime.datetime.now(utc_plus_1)
    yesterday = now_utc_plus_1 - datetime.timedelta(days=1)

    created_datasets = []
    updated_datasets = []
    
  # Browse datasets in catalogue, check if dataset was created or updated since yesterday, and if so create or update it on i14y
    for row in catalog['result']['rows']:
        
        created_date  = parser.parse(row['created']) # parse the timestamp as a date in UTC+1
        changed_date  = parser.parse(row['changed']) # parse the timestamp as a date in UTC+1
        
        if created_date > yesterday:
            identifier_created = row['idno']
            created_datasets.append(identifier_created)
            dataset = s.get(url = GET_ENDPOINT_FROM_UNISANTE + identifier_created, verify=False, timeout=40.0)
            dataset.raise_for_status()
            if dataset.status_code < 400:
                mapped_dataset = map_dataset(dataset.json())
                try:
                    post_dataset = post_data_to_i14y(json.dumps(mapped_dataset), ACCESS_TOKEN)
                    change_level_i14y(id, 'Public', ACCESS_TOKEN) # set dataset to public
                    change_status_i14y(id, 'Registered', ACCESS_TOKEN) # set dataset to registered
                    
                    previous_IDS_I14Y[identifier_created] = {'id': post_dataset.json()}
                    IDS_I14Y = json.dumps(previous_IDS_I14Y)
                    save_data(IDS_I14Y, path_to_data)

                except Exception as e:
                    print(f"Error in update_data: {e}")
                    raise
                    
        elif changed_date > yesterday:    
            identifier_updated = row['idno']
            updated_datasets.append(identifier_updated)
            dataset = s.get(url = GET_ENDPOINT_FROM_UNISANTE + identifier_updated, verify=False, timeout=40.0)
            dataset.raise_for_status()
            if dataset.status_code < 400:
                mapped_dataset = map_dataset(dataset.json())
                id = previous_IDS_I14Y[identifier_updated]['id']
                try:
                    put_data_to_i14y(id, json.dumps(mapped_dataset), ACCESS_TOKEN)

                    IDS_I14Y = previous_IDS_I14Y
                    IDS_I14Y = json.dumps(IDS_I14Y)
                    save_data(IDS_I14Y, path_to_data)

                except Exception as e:
                    print(f"Error in update_data: {e}")
                    raise

    # Create log to upload as artifact
    try:
        log = f"Harvest completed successfully at {datetime.datetime.now()}\n"
        log += "Created datasets:\n"
        for item in created_datasets:
            log += f"\n- {item}"
        log += "Updated datasets:\n"
        for item in updated_datasets:
            log += f"\n- {item}"
    except Exception as e:
        log = f"Harvest failed at {datetime.datetime.now()}: {str(e)}\n"
        raise
    finally:
        # Save log in root directory
        with open('harvest_log.txt', 'w') as f:
            f.write(log)
