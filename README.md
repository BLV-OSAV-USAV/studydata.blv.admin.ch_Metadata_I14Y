# I14Y Harvester for the FSVO data repository

## Features
- **Automated harvesting** (import new dataset and update existing datasets) via scheduled GitHub Actions.
- field mapping from DDI to DCAT
- script to harvest DDI datasets in json format

## Configuration 

**Environment Variables** 
Navigate to your GitHub repository:

- Settings → Secrets → Actions
- Add the following secrets (provided via encrypted email):
    - CLIENT_ID_PROD, CLIENT_SECRET_PROD (Production)
    - CLIENT_ID_ABN, CLIENT_SECRET_ABN (ABN)
             
**File Configuration**
Edit `src/config.py`:

```bash
PUBLISHER_ID = "your-publisher-id"  # Provided by BFS
HARVESTER_API_URL = ""  # API endpoint 
```

## Workflow

- The frequency at which the workflow runs is defined in the `.github/workflow` files.
- To trigger manually, go to GitHub → Actions → [Workflow] → Run Workflow.
- After each run, a log file is generated and uploaded as an artifact, which can be downloaded from the Actions tab.

## Setting for PROD

To set up the github action workflow fpr PROD, you just need to:
- uncomment the first line of the script `.github/workflows/harvester_prod.yml` and comment those lines in `.github/workflows/harvester_abn.yml`.
- chose the PROD API base URL in `src/config.py`

## Repository Structure

```
harvester_template/
├── .github/workflows                # GitHub Actions workflows fpr ABN and PROD
│   ├── harvester_abn.yml
│   └── harvester_prod.yml
├── src/ 
│    ├── config.py                   # Global settings 
│    ├── harvester.py                # Active harvester
│    └── field_mapping.py            # DDI to DCAT mapping
├── requirements.txt                 # Python dependencies 
└── README.md                        # This file
```
