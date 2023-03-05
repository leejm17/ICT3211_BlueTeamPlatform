""" Flask Configurations """
import os


"""Global Configs"""
class Config:
	APP_IP = "localhost"
	APP_PORT = 6065
	APP_DIR = "/home/{}/Documents/ICT3211_BlueTeamPlatform/application".format(os.getlogin())


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
