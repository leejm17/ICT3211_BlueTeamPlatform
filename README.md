# ICT3211_BlueTeamPlatform
A Python-based Web application platform that integrates open-source tools and in-house projects for the purpose of monitoring and analysing a Smart Meter Network System.

This Web application was developed in conjunction with a [RedTeamPlatform](https://github.com/leejm17/ICT3211_RedTeamPlatform) project.

Both projects are brought to you by IS Team 8 (AY 2022/23, Tri 2).


# Pre-requisites
This Web application was developed and has been tested successfully on **Ubuntu 22.04.1 LTS** (Jammy Jellyfish).

**Python 3.10.6** is the preferred Python version.

## Pre-existing Projects
This Web application has integrated certain in-house projects at the recommendation of academic researchers from the Singapore Institute of Technology (SIT). It is advised that the following projects be set-up appropriately in order to use the full suite of this Web application:
* [Arkime](https://arkime.com/index) (formerly Moloch) at Port 443.
* [Scrapyd](https://scrapyd.readthedocs.io/en/stable/index.html) at Port 6800.

## Pre-existing Applications
One of the features of this Web application is to provide users with an intuitive way to launch 5 pre-identified local applications without having to _Show Applications_. It is optional to install these local applications (FileZilla Client, Wireshark, Zui (Brim), DBeaver, Remmina).

Detailed instructions to install these 5 applications are described at the end of this README file (**[Install Local Applications](https://github.com/leejm17/ICT3211_BlueTeamPlatform#optional-install-local-applications)**).

## Installation Steps
You may choose to use a Virtual Environment if you wish to do so.

These are the installation steps to install software dependencies required to run the Web application smoothly, without ```venv```.

1. Update Ubuntu's repository sources.
```
sudo apt update
```

2. Install Python3 software packages required to run the Web application.
```
pip3 install -r requirements.txt
```

## Configuring IP address and Port
Python Flask offers the flexibility to specify the IP address and port number to run the Web application. Verify that your machine's IP address and port number tally with the following two variables in **/application/config.py**:
* APP_PORT=[Port number]
* APP_IP="[IP address]"

## Configuring Environment Variables
Environment variables are used by the Web application and should be stored in the root directory **/**. It is imperative to create the following environment files with verified values prior to launching the Web application.

#### 1. .arkime
Credentials to connect to the Arkime project.
```
ARKIME_USER='[username]'
ARKIME_PASSWORD='[password]'
```

#### 2. .database
Credentials to connect to the MySQL database.
```
DATABASE_DB='[database name]'
DB_HOST='[IP address of machine hosting the database]'
DB_PWD='[database password]'
DB_USER='[database username]'
SECRET_KEY='[Flask config's secret string, generated with Python secrets module]'
```
Following which, create a MySQL database to use the full suite of the integrated Spider feature.
1. Install MySQL.
```
sudo apt-get install mysql-server
```
2. Configure a Root password.
```
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '[new root password]';
```
3. Create a new database user for MySQL that has separate privileges from Root.
```
CREATE USER '[database username]'@'localhost' IDENTIFIED BY '[database password]';
```
4. Create a database for Spider if it does not exist on this MySQL instance.
```
CREATE DATABASE [database name];
```
5. Grant privileges to this database for the newly-created database user.
```
GRANT ALL ON [database name].* TO '[database username]'@'localhost';
exit
```
6. Import the database file **/scfami_spider.sql** as the newly-created database user.
```
mysql -u [database username] -p [database name] < scfami_spider.sql
```

#### 3. .datatransfer
Credentials to connect to FTPS Server on Smart Meter PC, and other settings.
```
CRON_USER='[Ubuntu's machine username]'
DEBIAN_IP='[IP address of Honeypot PC]'
FTP_PW='[FTPS password]'
FTP_USER='[FTPS username]'
WINDOWS_IP='[IP address of Smart Meter PC]'
WORKERS='[no. of workers to use for downloading of files via FTPS]'
```

#### 4. .networkcapture
Not sensitive, given in **/.networkcapture**.

## Other Configurations
By default, this Flask Web application is using a _Development_ configuration as seen on **Line 23** in **/application/app.py**.

If you wish to use the _Production_ configuration, ensure the following:
```
Line 23: #app.config.from_object("config.DevConfig")	# Using a development configuration
Line 24: app.config.from_object("config.ProdConfig")	# Using a production configuration
```

# Launching Web application
A start script has been developed to easily launch the Web application. This application hosted on a Python Flask server running on the local machine.

1. Move the **start_SCFAMI.sh** file to a directory of your choice.
2. Run the command ```sudo ./start_SCFAMI.sh``` to launch the Web application. This will start both the Web platform and backend Scrapy service daemon (_Scrapyd_) which will be used by the integrated Spider feature.

_Scrapyd requires administrative privileges to run its full features._


# Accessing the Web platform
Open your Web browser and go to your machine's IP address (the _APP_IP_ variable in **/application/config.py**) on **port 6065**.

Visit the FAQ page on the Web platform for detailed descriptions of the various features this Web application has to offer.

Enjoy!


# (Optional) Install Local Applications
Adding on to **[Pre-existing Applications](https://github.com/leejm17/ICT3211_BlueTeamPlatform#pre-existing-applications)** above, the installation of these 5 applications allow users to launch local applications that may aid in his/her analysis.

#### FileZilla Client
FileZilla Client is a FTP Client application to connect to FTP Servers.

Referencing an [article](https://linuxhint.com/filezilla-ftp-client-linux) by Denis Kariuki, there are two main steps to install FileZilla Client on Ubuntu 22.04.
```
sudo apt update             	# Update packages
sudo apt install filezilla -y	# Install FileZilla Client
```

#### Wireshark
Wireshark is a packet analyser, primarily used for analysing Packet Capture (PCAP) files.

Referencing an [article](https://linuxhint.com/install_wireshark_ubuntu) by Shahriar Shovon, there are four main steps to install Wireshark on Ubuntu.
```
sudo apt update                   	# Update packages
sudo apt install wireshark -y     	# Install Wireshark
    > Select <Yes> when prompted for non-superusers to capture packet.
sudo usermod -aG wireshark $(whoami)	# Add current user to Wireshark group
sudo reboot                        	# Recommended to reboot Ubuntu
```

#### Zui (Brim)
Zui (formerly Brim) is used to analyse structured data files.

[Download](https://www.brimdata.io/download) the **Desktop Application** for **Ubuntu/Debian**.

There are two main steps to install Zui on Ubuntu.
```
sudo apt update                         	# Update packages
sudo apt install ./[Zui package name].deb	# Install Zui
```

#### DBeaver
DBeaver is a SQL Client application to interact with databases.

[Download](https://dbeaver.io/download) the **Linux Debian package (installer)**.

There are two main steps to install DBeaver on Ubuntu.
```
sudo apt update                         	# Update packages
sudo apt install ./[DBeaver package name].deb	# Install DBeaver
```
Following which, connect to a SQL (MySQL) database to view .sql records

#### Remmina
Remmina is is a Remote Desktop Client application for POSIX-based operating systems.

It should have been shipped with any Ubuntu 22.04. Otherwise, there are two main steps to install it.
```
sudo apt update                            	# Update packages
sudo apt install remmina remmina-plugin-vnc	# Install Remmina
```
