'''
Provide a date range and optional API key and this script will get info for datasets and files created within that date range.
Useful when curating deposited data, especially spotting problem datasets (e.g. dataset with no data).
This script first uses the Search API to find PIDs of datasets.
For each dataset found, the script uses the "Get JSON" API endpoint to get dataset and file metadata of the latest version of each dataset,
and formats and writes that metadata to a CSV file on the users computer. Users can then analyze the CSV file (e.g. grouping, sorting, pivot tables)
for a quick view of what's been published within that date rage, what does and doesn't have files, and more.
'''

import csv
import json
import os
import sys
import urllib.request
from urllib.request import urlopen

# Get required info from user
server=''
startdate='' # yyyy-mm-dd
enddate='' # yyyy-mm-dd
apikey='' # for getting unpublished datasets accessible to Dataverse account
directory='' # directory for the CSV file containing the dataset and file info, e.g. '/Users/username/Desktop/'

# Initialization for paginating through results of Search API calls
start=0
condition=True

# List for storing indexed dataset PIDs and variable for counting misindexed datasets
dataset_pids=[]
misindexed_datasets_count=0

print('Searching for dataset PIDs:')
while (condition):
	try:
		per_page=10
		url='%s/api/search?q=*&fq=metadataSource:"Harvard+Dataverse"&type=dataset&per_page=%s&start=%s&sort=date&order=desc&fq=dateSort:[%sT00:00:00Z+TO+%sT23:59:59Z]&key=%s' %(server, per_page, start, startdate, enddate, apikey)
		data=json.load(urlopen(url))

		# Get total number of results
		total=data['data']['total_count']

		# For each item object...
		for i in data['data']['items']:

			# Get the dataset PID and add it to the dataset_pids list
			global_id=i['global_id']
			dataset_pids.append(global_id)

		print('Dataset PIDs found: %s of %s' %(len(dataset_pids), total), end='\r', flush=True)

		# Update variables to paginate through the search results
		start=start+per_page

	# If misindexed datasets break the Search API call, for the next 10 items try paginating with 1 item at a time. (See https://github.com/IQSS/dataverse/issues/4225)
	except urllib.error.URLError:
		try:
			per_page=1
			url='%s/api/search?q=*&fq=metadataSource:"Harvard+Dataverse"&type=dataset&per_page=%s&start=%s&sort=date&order=desc&fq=dateSort:[%sT00:00:00Z+TO+%sT23:59:59Z]&key=%s' %(server, per_page, start, startdate, enddate, apikey)
			data=json.load(urlopen(url))

			# Get dataset PID and save to dataset_pids list
			global_id=data['data']['items'][0]['global_id']
			dataset_pids.append(global_id)

			print('Dataset PIDs found: %s of %s' %(len(dataset_pids), total), end='\r', flush=True)

			# Update variables to paginate through the search results
			start=start+per_page

		# If page fails to load, count a misindexed dataset and continue to the next page
		except urllib.error.URLError:
			misindexed_datasets_count+=1
			start=start+per_page

	# Stop paginating when there are no more results
	condition=start<total

if misindexed_datasets_count:
	print('Datasets misindexed: %s\n' %(misindexed_datasets_count))

# If api key is used, deduplicate PIDs in dataset_pids list. (For published datasets with a draft version, the Search API lists the PID twice, once for published and draft versions.)
if apikey:
	unique_dataset_pids=set(dataset_pids)
	print('\nUnique datasets: %s (The Search API lists both the draft and most recently published versions of datasets)' %(len(unique_dataset_pids)))
# Otherwise, copy dataset_pids to unique_dataset_pids variable
else:
	unique_dataset_pids = dataset_pids

# Store name of CSV file, which includes the dataset start and end date range, to the 'filename' variable
filename='datasetinfo_%s-%s.csv' %(startdate.replace('-', '.'), enddate.replace('-', '.'))

# Create variable for directory path and file name
csvfilepath=os.path.join(directory, filename)

# Create CSV file
with open(csvfilepath, mode='w') as opencsvfile:
	opencsvfile=csv.writer(opencsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	
	# Create header row
	opencsvfile.writerow(['datasetURL (publicationState)', 'datasetTitle (dataverseName)', 'fileName (fileType, fileSize)'])

# For each data file in each dataset, add to the CSV file the dataset's URL and publication state, dataset title, data file name and data file contentType

print('\nWriting dataset and file info to %s:' %(csvfilepath))

# Create list to store any PIDs whose info can't be retrieved with "Get JSON" or Search API endpoints
piderrors=[]

# Function for converting bytes to more human-readable KB, MB, etc
def format_bytes(size):
    power=2**10
    n=0
    power_labels={0 : 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size>power:
        size/=power
        n+=1
    return '%s %s' %(round(size, 2), power_labels[n])

for pid in unique_dataset_pids:
	# Construct "Get JSON" API endpoint url and get data about each dataset's latest version
	try:
		if apikey:
			url='https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=%s&key=%s' %(pid, apikey)
		else:
			url='https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=%s' %(pid)
		# Store dataset and file info from API call to "data" variable
		data_getLatestVersion=json.load(urlopen(url))
	except urllib.error.URLError:
		piderrors.append(pid)

	# Construct "Search API" url to get name of each dataset's dataverse
	try:
		if apikey:
			url='%s/api/search?q="%s"&type=dataset&key=%s' %(server, pid, apikey)
		else:
			url='%s/api/search?q="%s"&type=dataset' %(server, pid)
		# Store Search API result to "data_dvName" variable
		data_dvName=json.load(urlopen(url))
	except urllib.error.URLError:
		piderrors.append(pid)

	# Save dataset title and dataverse name
	ds_title=data_getLatestVersion['data']['latestVersion']['metadataBlocks']['citation']['fields'][0]['value']
	dataverse_name=data_dvName['data']['items'][0]['name_of_dataverse']
	ds_title_dvName='%s (%s)' %(ds_title, dataverse_name)

	# Save dataset URL and publication state
	datasetPersistentId=data_getLatestVersion['data']['latestVersion']['datasetPersistentId']
	datasetURL='https://dataverse.harvard.edu/dataset.xhtml?persistentId=%s' %(datasetPersistentId)
	versionState=data_getLatestVersion['data']['latestVersion']['versionState']
	datasetURL_pubstate='%s (%s)' %(datasetURL, versionState)

	# If the dataset's latest version contains files, write dataset and file info (file name, contenttype, and size) to the CSV
	if data_getLatestVersion['data']['latestVersion']['files']:
		for datafile in data_getLatestVersion['data']['latestVersion']['files']:
			datafilename=datafile['label']
			datafilesize=format_bytes(datafile['dataFile']['filesize'])
			contentType=datafile['dataFile']['contentType']
			datafileinfo='%s (%s; %s)' %(datafilename, contentType, datafilesize)

			# Add fields to a new row in the CSV file
			with open(csvfilepath, mode='a', encoding='utf-8') as opencsvfile:

				opencsvfile=csv.writer(opencsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				
				# Create new row with dataset and file info
				opencsvfile.writerow([datasetURL_pubstate, ds_title_dvName, datafileinfo])

				# As a progress indicator, print a dot each time a row is written
				sys.stdout.write('.')
				sys.stdout.flush()

	# Otherwise print that the dataset has no files
	else:
		with open(csvfilepath, mode='a') as opencsvfile:

			opencsvfile=csv.writer(opencsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			
			# Create new row with dataset and file info
			opencsvfile.writerow([datasetURL_pubstate, ds_title_dvName, '(no files found)'])

			# As a progress indicator, print a dot each time a row is written
			sys.stdout.write('.')
			sys.stdout.flush()

print('\nFinished writing info of %s dataset(s) and their file(s) to %s' %(len(unique_dataset_pids), csvfilepath))

# If info of any PIDs could not be retrieved, print list of those PIDs
if piderrors:

	# Deduplicate list in piderrors variable
	piderrors=set(piderrors)

	print('Info about the following PIDs could not be retrieved. To investigate, try running "Get JSON" endpoint or Search API on these datasets:')
	print(*piderrors, sep='\n')