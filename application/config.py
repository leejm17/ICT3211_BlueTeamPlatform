""" Flask Configurations """
import os


class Config:
	DIRECTORY = "/home/{}/Documents/ICT3211_BlueTeamPlatform/application".format(os.getlogin())


class DevConfig(Config):
	FLASK_ENV = "development"
	DEBUG = True
	TESTING = True


class ProdConfig(Config):
	FLASK_ENV = "production"
	DEBUG = False
	TESTING = False
