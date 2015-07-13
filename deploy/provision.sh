#!/bin/sh

# Run as the root user when creating a DO server

# Setup a non root user
useradd --create-home --shell /bin/bash ubuntu
mkdir -p /home/ubuntu/.ssh
wget -O /home/ubuntu/.ssh/authorized_keys https://github.com/fonglh.keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
usermod -a -G sudo ubuntu

# Install MongoDB
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
apt-get update
apt-get install -y mongodb-org

# Install apache2 and PHP
apt-get install -y apache2
apt-get install -y php5 libapache2-mod-php5 php5-mcrypt

# Install PHP Pear and use it to install the PHP Mongo driver
apt-get install -y php5-dev php5-cli php-pear
pecl install mongo
echo "extension=mongo.so" >> /etc/php5/apache2/php.ini

# Install the PyMongo driver
apt-get install -y python-pip
apt-get install -y build-essential python-dev
pip install pymongo

# Install BeautifulSoup
apt-get install -y python-bs4
