Singapore PSI Plot
========

[![Build Status](https://travis-ci.org/fonglh/psi-plot.svg?branch=master)](https://travis-ci.org/fonglh/psi-plot)

Scripts to scrape NEA PSI data and display it in a graph

## Software Installation

1. Install apache2 and PHP
  1. `sudo apt-get install apache2`
  1. `sudo apt-get install php5 libapache2-mod-php5 php5-mcrypt`
1. Install MongoDB
  1. Look up the latest instructions from MongoDB.
1. Install PHP Pear and use it to install the PHP Mongo driver
  1. `sudo apt-get install php5-dev php5-cli php-pear`
  1. `sudo pecl install mongo`
  1. Add `extension=mongo.so` into the `php.ini` file
1. Install PyMongo driver
  1. `sudo apt-get install python-pip`
  1. `sudo apt-get install build-essential python-dev`
  1. `sudo pip install pymongo`
1. Install BeautifulSoup
  1. `sudo apt-get install python-bs4`

### The Lazy Way

1. Run `deploy/provision.sh` as the root user.
  1. A `ubuntu` user will be created and added to the sudo group
  1. You will be prompted for a password near the end of the script
  1. If you're not me, you probably want to change the part where the public keys are downloaded
  1. Some user input is still necessary
    1. Some mongo setup option
    1. ubuntu user sudo password
    1. Setting the timezone
1. Continue with the [Configuration](#configuration) section

## Configuration

1. Set the timezone to Singapore (because these are SG PSI readings)
  1. `sudo dpkg-reconfigure tzdata`
  1. Make the appropriate selections
1. Clone this repository
  1. Create a symlink to the `website` folder from the apache2 webroot folder `/var/www/html`
1. Restore Mongo data
  1. Make sure the database backup folder is a child of the `dump` folder
  1. Run `mongorestore` from the same level as the `dump` folder
1. Create a user for the `psi_db` database (not necessary if the dump folder has the user data)
  1. From the mongo client, `use psi_db`
  1. `db.createUser({user: "psiuser", pwd: "somepass", roles: [{role: "readWrite", db: "psi_db"}]})`
1. Reboot the server so the PHP Mongo setting will take effect

### Backing up the data

Just run `mongodump`

## Test the setup

1. Run the `getpsi.py` script from the repository. It should show today's scraped data.
1. Create a cronjob to run the script periodically
  1. `crontab -e`
  1. `*/10 * * * * /path/to/getpsi.py`
