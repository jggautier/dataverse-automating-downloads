# dataverse-scripts

Scripts for automating things in a Dataverse repository/installation, plus some other scripts. The scripts are written using Python 3 and a Mac OS. Compatability with Python 2 and Windows is limited, although I plan to improve compatibility with Windows over time. 

### get_dataset_PIDs.py
Gets the persistent identifiers of any datasets in a given Dataverse installation or a given Dataverse collection within that installation (and optionally all of the Dataverse collections within that Dataverse collection)

### These scripts do things with a given list of dataset PIDs or Dataverse collection IDs or aliases:

- #### change_citation_dates.py
- #### delete_dataset_locks.py
- #### delete_dataverses.py
- #### destroy_datasets.py
- #### [Get and convert metadata of datasets](https://github.com/jggautier/dataverse_scripts/tree/main/get-dataverse-metadata):
  A collection of scripts for getting JSON metadata of given datasets and parsing metadata into csv files for metadata analysis, reporting and improving.
- #### get_dataset_lock_info.py
- #### move_datasets.py
- #### publish_multiple_datasets.py
- #### remove_dataset_links.py
- #### replace_dataset_metadata.py

### curation_report.py
This script creates an overview of datasets created in a Dataverse installation in a given time frame, which can be useful for regular dataset curation.

### get_dataset_metadata_of_all_installations.py
This script downloads dataset metadata of as many known Dataverse installations as possible. Used to create the dataset at https://doi.org/10.7910/DVN/DCDKZQ.

### Misc
- #### combine_tables.py
  This script does a join on CSV files in a given directory.
- #### split_table.py
  This script splits a given CSV file into many csv files based on the unique values in a given column.
  
## Installation
 * Install Python 3 and pip if you don't already have it. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this GitHub repository](https://github.com/jggautier/dataverse_scripts/archive/refs/heads/main.zip) or clone this GitHub repository:

```
git clone https://github.com/jggautier/get-dataverse-metadata.git
```

 * Check if you have pipenv installed (`pipenv --version`) or install pipenv (`pip install pipenv`)

 * cd into the dataverse_scripts directory and install packages
 ```
pip install -r requirements.txt
```

* Use pipenv when running the scripts so that the installed packages are available to your script (`pipenv python change_citation_dates.py`). You can also use `pipenv shell` once so that all following commands have access to your installed packages.
