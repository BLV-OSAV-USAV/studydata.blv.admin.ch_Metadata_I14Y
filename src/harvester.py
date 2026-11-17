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


def find_i14y_dataset(session, identifier):
    """Return the unique target dataset, or None if it has not been imported."""
    response = session.get(
        url=config.API_BASE_URL + 'datasets',
        params={'datasetIdentifier': identifier, 'page': 1, 'pageSize': 25},
        headers={'Authorization': config.API_TOKEN, 'Accept': 'application/json'},
        verify=False,
        timeout=40.0,
    )
    response.raise_for_status()
    matches = response.json()['data']
    if len(matches) > 1:
        raise ValueError(f"Multiple I14Y datasets found for {identifier}; cannot choose an update target.")
    return matches[0] if matches else None


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
    unchanged_datasets = []
    rows = catalog['result']['rows']
    print(f"Katalog: {len(rows)} Datensätze; Stichtag: {yesterday.isoformat()}")

    try:
        for row in rows:
            identifier = row['idno']
            created_date = parser.parse(row['created'])
            changed_date = parser.parse(row['changed'])
            print(f"Prüfe {identifier}: erstellt={row['created']}, geändert={row['changed']}")

            # Check existence even for source datasets older than the cutoff.
            target = find_i14y_dataset(s, identifier)
            if target is not None and max(created_date, changed_date) <= yesterday:
                unchanged_datasets.append(identifier)
                print(f"Bereits auf I14Y vorhanden und unverändert: {identifier} (I14Y-ID: {target['id']})")
                continue

            dataset = s.get(url=config.HARVEST_API_URL + identifier, verify=False, timeout=40.0)
            dataset.raise_for_status()
            payload = json.dumps(get_field_mapping(dataset.json()))
            if target is None:
                post_data_to_i14y(payload, config.API_TOKEN)
                created_datasets.append(identifier)
                print(f"Auf I14Y erstellt: {identifier}")
                # Resolve the new ID rather than using an unrelated previous ID.
                target = find_i14y_dataset(s, identifier)
                if target is None:
                    raise RuntimeError(f"{identifier} wurde erstellt, ist aber noch nicht auffindbar; Publikation und Registrierung konnten nicht gesetzt werden.")
                change_level_i14y(target['id'], 'Public', config.API_TOKEN)
                change_status_i14y(target['id'], 'Registered', config.API_TOKEN)
            else:
                put_data_to_i14y(target['id'], payload, config.API_TOKEN)
                updated_datasets.append(identifier)
                print(f"Auf I14Y aktualisiert: {identifier} (I14Y-ID: {target['id']})")

    finally:
        # Print the same report that is uploaded as an artifact.
        sections = [
            ("Auf I14Y erstellt", created_datasets),
            ("Auf I14Y aktualisiert", updated_datasets),
            ("Bereits auf I14Y vorhanden und unverändert", unchanged_datasets),
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
