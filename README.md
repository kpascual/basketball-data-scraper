# PLAY BY PLAY AND BOX SCORE SCRAPING LIBRARY


## Requirements


This library was created on a Mac, so the setup instructions are geared toward a *nix environment (sorry Windows users)

* Python 2.5 or greater
* BeautifulSoup4 (pip install beautifulsoup4)
* lxml (used within BeautifulSoup) (pip install lxml)


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

* Run the build.sh script


```
sh build.sh database_username database_password database_name
```

To actually do scraping, run the scrape.py file. You will be asked what league you want to run.

```
python scrape.py
```

