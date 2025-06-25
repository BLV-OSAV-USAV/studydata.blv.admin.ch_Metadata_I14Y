import os

###########################################
#Harvesting configuration API or FILE 
###########################################

HARVEST_API_URL = "https://www.studydata.blv.admin.ch/api/catalog/"

###########################################
# I14Y API configuration
###########################################

# API_BASE_URL = "https://api.i14y.admin.ch/api/partner/v1/" # Prod environement 
API_BASE_URL = "https://api-a.i14y.admin.ch/api/partner/v1/" # ABN enironement 
API_TOKEN = f"Bearer {os.environ['ACCESS_TOKEN']}" 

# Organization settings
ORGANIZATION_ID = "CH_BLV"
DEFAULT_PUBLISHER = {
    "identifier": ORGANIZATION_ID
}


