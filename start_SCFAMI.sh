#!/bin/sh
# This script can be launched from anywhere on your system.
# A suggestion is the ~/home/$USER/Desktop folder.

# Change this to $whoami without sudo
USER="ubuntu"

# Kill previous instance of scrapyd
kill $(pgrep -f scrapyd)

# Start Scrapyd
cd /home/$USER/Documents/scfami_spider/yara_scrapy
#echo $(pwd)
scrapyd >> scrapyd-logs.txt &

# Start Flask
cd /home/$USER/Desktop
#echo $(pwd)
FLASK_DIRECTORY="/home/$USER/Documents/ICT3211_BlueTeamPlatform/application"
sudo -u $USER python3 $FLASK_DIRECTORY/app.py
