def map_dataset(input_data):

    output_data = {
        "data": {
          "accessRights": {
            "code": "RESTRICTED"
          },
          "conformsTo": [],
          "contactPoints": [],
          "description": {
            "en": input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("study_info", {}).get("abstract")
            },
          "distributions": [],
          "documentation": [],
          "geoIvIds": [],
          "identifiers": [input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("title_statement", {}).get("idno")],
          "issued": input_data.get("dataset", {}).get("created"),
          "keywords": [],
          "landingPages": [
              {
                "uri": input_data.get("dataset", {}).get("link_study"),
                "label": {}
              }
            ],      
          "languages": [],
          "modified": input_data.get("dataset", {}).get("changed"),
          "publisher": {
              "id": "f9a1fab2-611d-4e8a-943e-ddd133f982bf",
              "identifier": "CH_BLV",
              "name": {
                "de": "Bundesamt für Lebensmittelsicherheit und Veterinärwesen",
                "en": "Federal Food Safety and Veterinary Office",
                "fr": "Office fédéral de la sécurité alimentaire et des affaires vétérinaires",
                "it": "Ufficio federale della sicurezza alimentare e di veterinaria"
              }
            },
          "qualifiedAttributions": [
              {
                "agent": {
                  "id": "f38c9441-0989-4614-b96d-df996b74140e",
                  "identifier": "Unisante",
                  "name": {
                    "en": "Center for Primary Care and Public Health (Unisanté), University of Lausanne, Switzerland"
                  }
                },
                "hadRole": {
                  "code": "distributor"
                },
              }
            ],
          "qualifiedRelations": [
            {
              "hadRole": {
                "code": "original",
                "name": {
                  "de": "Original",
                  "en": "Original",
                  "fr": "Original",
                  "it": "Originale"
                },
                "uri": "http://www.iana.org/assignments/relation/original"
              },
              "relation": {
                "uri": "https://www.studydata.blv.admin.ch/catalog/4", #input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("data_access", {}).get("dataset_availability", {}).get("access_place_uri"),
                "label": {}
              }
            }
          ],
          "relations": [],
          "spatial": [
          input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("study_info", {}).get("geog_coverage")
          ],
          "temporalCoverage": [],
          "themes": [
            {
              "code": "114"
            }
          ],
          "title": {
            "en": input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("title_statement", {}).get("title")
          },
          "version": input_data.get("dataset", {}).get("metadata", {}).get("doc_desc", {}).get("version_statement", {}).get("version"),
          "versionNotes": {
            "en": input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("version_statement", {}).get("version")
          }
        }
      }


    tags = input_data.get("dataset", {}).get("metadata", {}).get("tags", [])
    containPerson = False
    for tag in tags:
        if tag['tag'] == 'Humans': containPerson = True
    if containPerson: output_data["data"]["confidentialityPerson"] = { "code": "person" } # protected person?
    else: output_data["data"]["confidentialityPerson"] = { "code": "no_person" }

    keywords = input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("study_info", {}).get("keywords", [])
    for keyword in keywords:
        output_data["data"]["keywords"].append({"en": keyword.get("keyword","")})  


    contacts = input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("distribution_statement", {}).get("contact", [])
    for contact in contacts:
        output_data["data"]["contactPoints"].append({
          "hasAddress": {},
          "kind": "Organization",
          "hasEmail": contact.get("email",""),
          "fn": {
            "en": contact.get("name","")
          },
          "note": {},
          "hasTelephone": ""
        })
    
    temporalCoverage = input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("study_info", {}).get("coll_dates",[])
    for coverage in temporalCoverage:
        output_data["data"]["temporalCoverage"].append({
          "start": coverage["start"],
          "end": coverage["end"] 
        }) 

    output_data["data"]["distributions"].append({       
              "accessUrl": {
                "label": {
                  "en": "FSVO Data repository" # input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("data_access", {}).get("dataset_availability", {}).get("access_place")
                },
                "uri": "https://www.studydata.blv.admin.ch/catalog/4" # input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("data_access", {}).get("dataset_availability", {}).get("access_place_uri")
              },
              "conformsTo": [],
              "coverage": [],
              "description": {
                 "en": input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("data_access", {}).get("dataset_use", {}).get("conditions")          
              },
              "documentation": [],
              "images": [],
              "languages": [],
              "title": {
                "en": input_data.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("title_statement", {}).get("title")
              }
            })

    for coverage in temporalCoverage:
            output_data["data"]["distributions"][0]["coverage"].append({
              "start": coverage["start"],
              "end": coverage["end"] 
                    }) 

    return output_data
