'''
This script takes the metadatablock files retrieved by the get_dataset_metadata_of_all_installations.py script
and adds the metadatablock names and fields of each installation into a CSV file for further analysis.
'''

import csv
import json
import os
from pathlib import Path


# Function for getting list of non-hidden directories inside of a given directory
def listdir_nohidden(path):
    directories = []
    for f in os.listdir(path):
        if not f.startswith('.'):
            directories.append(f)
    return directories


# Enter path to directory that contains the folders and files created by the get_dataset_metadata_of_all_installations.py script
mainDirectory = ''

# Enter path to directory to store CSV file that this script will create
csvFileFolder = ''

csvFile = str(Path(csvFileFolder + '/' + 'metadatablocks.csv'))

with open(csvFile, mode='w') as data:
    data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Create header row
    data.writerow([
        'installation_name_(Dataverse_version)', 'metadatablock_name', 
        'parentfield_name', 'subfield_name'])

count = 0
total = len(listdir_nohidden(mainDirectory))

# for repositoryFileName in os.listdir(mainDirectory):
for repositoryFileName in listdir_nohidden(mainDirectory):

    count += 1

    # Get the repository name
    size = len(repositoryFileName)
    repositoryName = repositoryFileName[:size - 20]
    print(f'Parsing metadatablocks: {count} of {total}')

    # Open each installation folder
    repositoryFolderPath = str(Path(mainDirectory + '/' + repositoryFileName))
    if os.path.isdir(repositoryFolderPath):

        for subFolder in os.listdir(repositoryFolderPath):
            if 'metadatablocks' in subFolder:
                metadatablockFolderPath = str(Path(repositoryFolderPath + '/' + subFolder))

        # Open each .json file
        for metadatablockFile in os.listdir(metadatablockFolderPath):

            # Get only the metadatablock name from the name of each metadatablock JSON file
            metadatablockName = metadatablockFile.split('_', 1)[0]
            version = metadatablockFile.split('_v', 1)[1].rstrip('.json')

            # Get repository name and combine with version
            repositoryNameVersion = '%s_(%s)' % (repositoryName, version)

            metadatablockFilePath = str(Path(metadatablockFolderPath + '/' + metadatablockFile))

            with open(metadatablockFilePath, 'r') as f:  # Open file in read mode
                metadatablockData = f.read()  # Copy content to dataset_metadata variable
                metadatablockData = json.loads(metadatablockData)  # Load content as a python dict

                # Get the names of fields that have childfields
                compoundfields = []
                for parentfield in metadatablockData['data']['fields']:
                    properties = metadatablockData['data']['fields'][parentfield]
                    for property in properties:
                        if 'childFields' in properties:
                            field = properties[property]
                            compoundfields.append(field)
                            break

                allParentAndChildFields = []
                for parentfield in compoundfields:
                    if parentfield in metadatablockData['data']['fields']:
                        properties = metadatablockData['data']['fields'][parentfield]['childFields']
                        allParentAndChildFields.append(parentfield)
                        for subfield in properties:
                            allParentAndChildFields.append(subfield)

                            # Add parent and child names to the CSV file
                            with open(csvFile, mode='a') as data:
                                data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                # Write new row
                                data.writerow([repositoryNameVersion, metadatablockName, parentfield, subfield])

                # Get the names of all fields
                allFields = []
                for parentfield in metadatablockData['data']['fields']:
                    properties = metadatablockData['data']['fields'][parentfield]
                    for property in properties:
                        field = properties[property]
                        allFields.append(field)
                        break

                # Get names of primitives fields by removing list of compound and child fields from the list of all fields
                primitiveFields = list(set(allFields) - set(allParentAndChildFields))

                # Add the primitive field names to the CSV file
                for primitiveField in primitiveFields:

                    # Set subfield to an empty string so that Dataverse ingests the CSV file.
                    # (Dataverse's ingest process doesn't seem to like it when there is nothing entered in the fourth column)
                    subfield = ''
                    with open(csvFile, mode='a') as data:
                        data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        # Write new row
                        data.writerow([repositoryNameVersion, metadatablockName, primitiveField, subfield])
