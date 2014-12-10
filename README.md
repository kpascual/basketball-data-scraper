# PLAY BY PLAY AND BOX SCORE SCRAPING LIBRARY


## Requirements


This library was created on a Mac, so the setup instructions are geared toward a *nix environment (sorry Windows users)

* Python 2.5 or greater
* MySQL
* BeautifulSoup4 (pip install beautifulsoup4)
* lxml (used within BeautifulSoup) (pip install lxml)
* MySQLdb - Python's API to the MySQL database (pip install MySQL-python)


## Instructions


* Clone the repository to your local machine (change your_folder_path to whatever folder you want to put the repo)

```
cd your_folder_path
git clone git@github.com:kpascual/basketball-data-scraper.git
```

* Add this new directory to your PYTHONPATH in ~/.bash_profile

```
PYTHONPATH="/your_folder_path/basketball-data-scraper:$PYTHONPATH"
export PYTHONPATH
```

* Go to the config/ folder
* Copy config/constants_example.py to config/constants.py, and edit rows 3-8 in constants.py with the path containing this repo.

```
cp config/constants_example.py config/constants.py
```

* Copy configg_example.py to configg.py

```
cp configg_example.py configg.py
```

* In configg.py, enter your MySQL database credentials
```
vi db.py

  4 prod = {
  5     'user': 'username_for_database',
  6     'passwd': 'password__for_database',
  7     'db': 'production_database_name'
  8 }
```

* TODO: seed initial schema

```
cd your_path_here/schema
mysql -u user_name -p database_name < core_schema.sql
mysql -u user_name -p database_name < core_data.sql
mysql -u user_name -p database_name < game_data.sql
```

To actually do scraping, run the scrape.py file. You will be asked what league you want to run.

```
python scrape.py
```

