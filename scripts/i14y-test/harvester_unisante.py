import requests
import json
import os
import datetime
from mapping_unisante import map_dataset

GET_ENDPOINT_FROM_UNISANTE = os.environ['GET_ENDPOINT_FROM_UNISANTE']
PUT_ENDPOINT_TO_I14Y = os.environ['PUT_ENDPOINT_TO_I14Y']$
IDS_I14Y = json.loads(os.environ['IDS_I14Y'])
ACCESS_TOKEN = f"Bearer {os.environ['ACCESS_TOKEN']}" 

def put_data_to_i14y(endpoint, params, data, token):
    response = requests.put(endpoint, params=params, data=data, headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, verify=False)
    response.raise_for_status()
    return response.json()

def get_data_from_i14y(endpoint, params, token):
    response = requests.put(endpoint, params=params, headers={'Authorization': token, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'}, verify=False)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":

    s = requests.Session()

  # Get catalogue from Unisante
    response = s.get(url = GET_ENDPOINT_FROM_UNISANTE + 'search', verify=False, timeout=40.0)
    catalog = response.json()
  
  # Browse datasets in catalogue, check if dataset was updated since yesterday and if so update it on i14y
    for row in catalog['result']['rows']:
          changed_date  = parser.parse(row['created']) # parse the timestamp as date in UTC+1
          utc_plus_1 = datetime.timezone(datetime.timedelta(hours=1))
          now_utc_plus_1 = datetime.datetime.now(utc_plus_1)
          yesterday = now_utc_plus_1 - datetime.timedelta(days=1)
    
          if changed_date > yesterday:    
            identifier = row['idno']
              dataset = s.get(url = GET_ENDPOINT_FROM_UNISANTE + identifier, verify=False, timeout=40.0)
              dataset.raise_for_status()
              if dataset.status_code < 400:
                  mapped_dataset = map_dataset(dataset.json())
                  id = IDS_I14Y[identifier]['id']
                  try:
                    put_data_to_i14y(
                      endpoint = PUT_ENDPOINT_TO_I14Y,
                      params = {'id': id},
                      data = json.dumps(mapped_dataset),
                      token=ACCESS_TOKEN
                    )
            
                  except Exception as e:
                      print(f"Error in update_data: {e}")
                      raise
    
    try:
        log = f"Harvest completed successfully at {datetime.now()}\n"
    except Exception as e:
        log = f"Harvest failed at {datetime.now()}: {str(e)}\n"
        raise
    finally:
        # Save log in root directory
        with open('harvest_log.txt', 'w') as f:
            f.write(log)
