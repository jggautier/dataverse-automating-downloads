# For a given list of datasets, changes the date used in the dataset citation from the default 
# (date when datasets were first published in the Dataverse repository) to the date in another date 
# metadata field, e.g. distributionDate

import urllib.request

server=''
apikey=''
data=b'distributionDate'
pids=[]
count=0

for pid in pids:

	url='%s/api/datasets/:persistentId/citationdate?persistentId=%s' %(server, pid)

	headers={
		'X-Dataverse-key':apikey
		}

	req=urllib.request.Request(
		url=url,
		data=data,
		headers=headers,
		method='PUT'
		)

	response=urllib.request.urlopen(req)

	count+=1

	print('Changing citation dates: %s of %s datasets' %(count, len(pid)), end='\r', flush=True)