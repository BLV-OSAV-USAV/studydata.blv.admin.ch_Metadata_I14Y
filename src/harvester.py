import requests
import json
import os
import urllib3
import datetime
from dateutil import parser
from typing import Dict, Any

import config
from mapping import get_field_mapping

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def put_data_to_i14y(id, data, token):
    """Modifiy an exisitng dataset"""

    response = requests.put(
        url = config.API_BASE_URL + 'datasets/' + id,
        data=data, 
        headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
        verify=False
    )
    response.raise_for_status()
    return response.json()


def post_data_to_i14y(data, token):
    """Import a new dataset"""

    response = requests.post(
        url = config.API_BASE_URL + 'datasets',
        data=data, 
        headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
        verify=False
    )
    response.raise_for_status()
    return response.json()


def change_level_i14y(id, level, token):
    """Change the publication level of the dataset"""

    response = requests.put(
            url = config.API_BASE_URL + 'datasets/' + id + '/publication-level',
            params = {'level': level}, 
            headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
            verify=False
        )
    response.raise_for_status()
    return response.json()

def change_status_i14y(id, status, token):
    """Change the registration status of the dataset"""

    response = requests.put(
            url = config.API_BASE_URL + 'datasets/' + id + '/registration-status',
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
    
    s = requests.Session()

  # Get FSVO catalogue 
    response = s.get(url = config.HARVEST_API_URL + 'search', verify=False, timeout=40.0)
    catalog = response.json()

  # Get yesterday's date in UTC+1
    utc_plus_1 = datetime.timezone(datetime.timedelta(hours=1))
    now_utc_plus_1 = datetime.datetime.now(utc_plus_1)
    yesterday = now_utc_plus_1 - datetime.timedelta(days=1)

    created_datasets = []
    updated_datasets = []
    
  # Browse datasets in catalogue, check if each dataset was created or updated since yesterday, and create or update it on i14y accordingly
    for row in catalog['result']['rows']:
        
        created_date  = parser.parse(row['created']) # parse the timestamp as a date in UTC+1
        changed_date  = parser.parse(row['changed']) # parse the timestamp as a date in UTC+1
        
        # New dataset
        if created_date > yesterday:
            identifier_created = row['idno']
            created_datasets.append(identifier_created)
            dataset = s.get(url = config.HARVEST_API_URL + identifier_created, verify=False, timeout=40.0)
            dataset.raise_for_status()
            if dataset.status_code < 400:
                mapped_dataset = get_field_mapping(dataset.json())
                try:
                    post_dataset = post_data_to_i14y(json.dumps(mapped_dataset), config.ACCESS_TOKEN)
                    change_level_i14y(id, 'Public', config.ACCESS_TOKEN) # set dataset to public
                    change_status_i14y(id, 'Registered', config.ACCESS_TOKEN) # set dataset to registered

                except Exception as e:
                    print(f"Error in update_data: {e}")
                    raise

        # Udpated dataset           
        elif changed_date > yesterday:    
            identifier_updated = row['idno']
            updated_datasets.append(identifier_updated)
            dataset = s.get(url = config.HARVEST_API_URL + identifier_updated, verify=False, timeout=40.0)
            dataset.raise_for_status()
            if dataset.status_code < 400:
                mapped_dataset = get_field_mapping(dataset.json())

                # get the dataset id
                i14y_dataset = s.get(
                    url = config.API_BASE_URL + 'datasets?datasetIdentifier=' + identifier_updated + '&page=1&pageSize=25',
                    headers={'Authorization': config.ACCESS_TOKEN, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, 
                    verify=False
                )
                id = i14y_dataset.json()['data'][0]['id']

                try:
                    put_data_to_i14y(id, json.dumps(mapped_dataset), config.ACCESS_TOKEN)

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
