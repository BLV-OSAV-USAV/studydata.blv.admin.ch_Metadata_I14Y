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
    response.raise_for_status()
    catalog = response.json()

  # Get yesterday's date in UTC+1
    utc_plus_1 = datetime.timezone(datetime.timedelta(hours=1))
    now_utc_plus_1 = datetime.datetime.now(utc_plus_1)
    #yesterday = now_utc_plus_1 - datetime.timedelta(days=1)

    yesterday = datetime.datetime(2026, 2, 16, 0, 0, tzinfo=utc_plus_1)

    created_datasets = []
    updated_datasets = []
    skipped_datasets = []
    unchanged_datasets = []
    rows = catalog['result']['rows']
    print(f"Katalog: {len(rows)} Datensätze; Stichtag: {yesterday.isoformat()}")

    try:
      # Browse datasets in catalogue, check if each dataset was created or updated since yesterday, and create or update it on i14y accordingly
        for row in rows:

            created_date  = parser.parse(row['created']) # parse the timestamp as a date in UTC+1
            changed_date  = parser.parse(row['changed']) # parse the timestamp as a date in UTC+1

            print(f"Prüfe {row['idno']}: erstellt={row['created']}, geändert={row['changed']}")

            # New dataset
            if created_date > yesterday:
                identifier_created = row['idno']
                dataset = s.get(url = config.HARVEST_API_URL + identifier_created, verify=False, timeout=40.0)
                dataset.raise_for_status()
                if dataset.status_code < 400:
                    mapped_dataset = get_field_mapping(dataset.json())
                    try:
                        post_dataset = post_data_to_i14y(json.dumps(mapped_dataset), config.API_TOKEN)
                        created_datasets.append(identifier_created)
                        print(f"Auf I14Y erstellt: {identifier_created}")
                        change_level_i14y(id, 'Public', config.API_TOKEN) # set dataset to public
                        change_status_i14y(id, 'Registered', config.API_TOKEN) # set dataset to registered

                    except Exception as e:
                        print(f"Error in update_data: {e}")
                        raise

            # Udpated dataset
            elif changed_date > yesterday:
                identifier_updated = row['idno']
                dataset = s.get(url = config.HARVEST_API_URL + identifier_updated, verify=False, timeout=40.0)
                dataset.raise_for_status()
                if dataset.status_code < 400:
                    mapped_dataset = get_field_mapping(dataset.json())

                    # get the dataset id
                    i14y_dataset = s.get(
                        url = config.API_BASE_URL + 'datasets',
                        params = {'datasetIdentifier': identifier_updated, 'page': 1, 'pageSize': 25},
                        headers={'Authorization': config.API_TOKEN, 'Content-Type': 'application/json', 'Accept': '*/*','Accept-encoding': 'json'},
                        verify=False
                    )
                    i14y_dataset.raise_for_status()
                    matches = i14y_dataset.json()['data']
                    if not matches:
                        print(f"Skipping {identifier_updated}: no matching dataset found in I14Y.")
                        skipped_datasets.append(identifier_updated)
                        continue
                    if len(matches) > 1:
                        raise ValueError(f"Multiple I14Y datasets found for {identifier_updated}; cannot choose an update target.")
                    id = matches[0]['id']

                    try:
                        put_data_to_i14y(id, json.dumps(mapped_dataset), config.API_TOKEN)
                        updated_datasets.append(identifier_updated)
                        print(f"Auf I14Y aktualisiert: {identifier_updated} (I14Y-ID: {id})")

                    except Exception as e:
                        print(f"Error in update_data: {e}")
                        raise

            else:
                unchanged_datasets.append(row['idno'])
                print(f"Übersprungen: {row['idno']} – seit dem Stichtag weder erstellt noch geändert.")

    finally:
        # Print the same report that is uploaded as an artifact.
        sections = [
            ("Auf I14Y erstellt", created_datasets),
            ("Auf I14Y aktualisiert", updated_datasets),
            ("Übersprungen: kein Treffer auf I14Y", skipped_datasets),
            ("Übersprungen: seit Stichtag unverändert", unchanged_datasets),
        ]
        lines = [
            f"Katalog: {len(rows)} Datensätze; Stichtag: {yesterday.isoformat()}",
            f"Auf I14Y geladen: {len(created_datasets) + len(updated_datasets)}",
        ]
        for label, identifiers in sections:
            lines.append(f"\n{label} ({len(identifiers)}):")
            lines.extend(f"- {identifier}" for identifier in identifiers)
        log = "\n".join(lines) + "\n"
        print(log)
        with open('harvest_log.txt', 'w') as f:
            f.write(log)
