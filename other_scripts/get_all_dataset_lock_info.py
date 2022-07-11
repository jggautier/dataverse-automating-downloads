import csv
from dateutil import tz
from dateutil.parser import parse
import json
import os
import requests
import time
import sys

sys.path.append('/Users/juliangautier/dataverse-scripts/dataverse_repository_curation_assistant')

from dataverse_repository_curation_assistant_functions import *

# From user get installation URL, apiToken, directory to save CSV file
installationUrl = ''
apiKey = ''
directoryPath = ''

# To search RT system for emails that locked dataset owners have sent to Dataverse support,
# include your RT username and password
rtUserLogin = ''
rtUserPassword = ''

# List PIDs of datasets whose problematic locks have already been reported
# e.g. in the Harvard Dataverse Repository GitHub repo issue at https://github.com/IQSS/dataverse.harvard.edu/issues/150)
ignorePIDs = [
    'doi:10.7910/DVN/GLMW3X', 
    'doi:10.7910/DVN/A3NWA7',
    'doi:10.7910/DVN/VYNLON',
    'doi:10.7910/DVN/RC0WLY'
    ]

# List lock types. See https://guides.dataverse.org/en/5.10/api/native-api.html?highlight=locks#list-locks-across-all-datasets
lockTypesList = ['Ingest', 'finalizePublication']

currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

datasetPids = []

# Get dataset PIDs of datasets that have any of the lock types in lockTypesList
for lockType in lockTypesList:

    datasetLocksApiEndpoint = f'{installationUrl}/api/datasets/locks?type={lockType}'
    response = requests.get(
        datasetLocksApiEndpoint,
        headers={'X-Dataverse-key': apiKey})
    data = response.json()

    if data['status'] == 'OK':
        for lock in data['data']:
            datasetPid = lock['dataset']
            datasetPids.append(datasetPid)

# Remove PIDs in ignorePIDs list from datasetPids list
datasetPids = [datasetPid for datasetPid in datasetPids if datasetPid not in ignorePIDs]

# Use set function to deduplicate datasetPids list and convert set to a list again
datasetPids = list(set(datasetPids))

total = len(datasetPids)

if total == 0:
    print(f'No locked datasets found (not including the {len(ignorePIDs)} datasets being ignored).')

elif total > 0:
    print(f'Locked datasets found: {total}\r\r')

    if rtUserLogin and rtUserPassword != '':
        import rt
        # Log in to RT to search for support emails from the dataset depositors
        print('Logging into RT support email system\r\r')
        tracker = rt.Rt('https://help.hmdc.harvard.edu/REST/1.0/', rtUserLogin, rtUserPassword)
        tracker.login()

    datasetCount = 0

    # Create CSV file and header row
    csvOutputFile = f'dataset_locked_status_{currentTime}.csv'
    csvOutputFilePath = os.path.join(directoryPath, csvOutputFile)

    with open(csvOutputFilePath, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow([
            'dataset_url', 'dataset_title', 'lock_reason', 'locked_date', 'user_name',
            'contact_email', 'possible_duplicate_datasets', 'rtticket_urls'])

        # For each dataset, write to the CSV file info about each lock the dataset has
        for datasetPid in datasetPids:

            datasetMetadata = get_dataset_metadata_export(
                installationUrl=installationUrl, datasetPid=datasetPid, 
                exportFormat='dataverse_json', header={}, apiKey=apiKey)

            # Get title of latest version of the dataset
            for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                if field['typeName'] == 'title':
                    datasetTitle = field['value']

            # Get contact email addresses of the dataset
            contactEmailsList = []

            for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                if field['typeName'] == 'datasetContact':
                    for contact in field['value']:
                        contactEmail = contact['datasetContactEmail']['value']
                        contactEmailsList.append(contactEmail)
            contactEmailsString = list_to_string(contactEmailsList)

            # Search for and return the DOIs of any other datasets with the same title

            # get_params function splits the searchApiURL on ampersands to find params,
            # so any ampersands in the title need to be replaced
            datasetTitle2 = datasetTitle.replace('&', '%26')

            rootAlias = get_root_alias_name(installationUrl)
            searchURL = f'{installationUrl}/dataverse/{rootAlias}?q=title:"{datasetTitle2}"'
            searchApiUrl = get_search_api_url(searchURL)

            requestsGetProperties = get_params(searchApiUrl)
            baseUrl = requestsGetProperties['baseUrl']
            params = requestsGetProperties['params']
            datasetInfoDF = get_object_dataframe_from_search_api(
                url=baseUrl, params=params, objectType='dataset', apiKey=apiKey)
            duplicateDatasetCount = len(datasetInfoDF.index)

            if duplicateDatasetCount <= 1:
                duplicateDatasetPidsString = 'No duplicate datasets found'
            elif duplicateDatasetCount >= 1:
                duplicateDatasetPidsList = []
                for dfIndex, dfRow in datasetInfoDF.iterrows():
                    duplicateDatasetPid = dfRow['dataset_pid']
                    if duplicateDatasetPid != datasetPid:
                        duplicateDatasetPidsList.append(duplicateDatasetPid)
                duplicateDatasetPidsString = list_to_string(duplicateDatasetPidsList)

            # If RT username and password is provided, log into RT and use the contact email addresses to
            # search for support emails from the dataset owner
            if rtUserLogin and rtUserPassword != '':
                
                rtTicketUrlsList = []
                for contactEmail in contactEmailsList:

                    # Search RT system for emails sent from the contact email address
                    searchResults = tracker.search(
                        Queue='dataverse_support', 
                        raw_query=f'Requestor.EmailAddress="{contactEmail}"')

                    # If there are any RT tickets found, save the ticket URL
                    if len(searchResults) > 0:
                        for rtTicket in searchResults:
                            rtTicketID = rtTicket['numerical_id']
                            rtTicketUrl = f'https://help.hmdc.harvard.edu/Ticket/Display.html?id={rtTicketID}'
                            rtTicketUrlsList.append(rtTicketUrl)

                        # Use set function to deduplicate rtTicketUrlsList list and convert set to a list again
                        rtTicketUrlsList = list(set(rtTicketUrlsList))

                        # Convert list of ticket URLs to a string (to add to CSV file later)
                        rtTicketUrlsString = list_to_string(rtTicketUrlsList)
                    if len(searchResults) == 0:
                        rtTicketUrlsString = 'No RT tickets found'

            # If no RT username or password are provided...
            elif rtUserLogin or rtUserPassword == '':
                rtTicketUrlsString = 'Not logged into RT. Provide RT username and password'

            # Get all data about locks on the dataset
            url = f'{installationUrl}/api/datasets/:persistentId/locks?persistentId={datasetPid}'
            allLockData = requests.get(url).json()

            datasetCount += 1

            for lock in allLockData['data']:
                datasetUrl = f'{installationUrl}/dataset.xhtml?persistentId={datasetPid}'
                reason = lock['lockType']
                lockedDate = convert_to_local_tz(lock['date'], shortDate=True)
                userName = lock['user']
                f.writerow([
                    datasetUrl, datasetTitle, reason, lockedDate, userName,
                    contactEmailsString, duplicateDatasetPidsString, rtTicketUrlsString])

                print(f'Recording information about {datasetCount} of {total} datasets: {datasetPid}')
