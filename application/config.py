""" Flask Configurations """
from admin import retrieve_database_var
import getpass


"""Global Configs"""
class Config:
	APP_IP = "localhost"	# "172.16.2.6"
	APP_PORT = 6065
	APP_DIR = "/home/{}/Documents/ICT3211_BlueTeamPlatform/application".format(getpass.getuser())

	# Flask DB Config
	db = retrieve_database_var()
	MYSQL_DATABASE_HOST = db["db_host"]
	MYSQL_DATABASE_DB = db["database_db"]
	MYSQL_DATABASE_USER = db["db_user"]
	MYSQL_DATABASE_PASSWORD = db["db_pwd"]
	SECRET_KEY = db["secret"]


"""Development Configuration"""
class DevConfig(Config):
	FLASK_ENV = "development"
	DEBUG = True
	TESTING = True


"""Production Configuration"""
class ProdConfig(Config):
	FLASK_ENV = "production"
	DEBUG = False
	TESTING = False
