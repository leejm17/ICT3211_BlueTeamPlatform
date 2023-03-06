""" Flask Configurations """
import getpass


"""Global Configs"""
class Config:
	APP_IP = "localhost"	# "172.16.2.6"
	APP_PORT = 6065
	APP_DIR = "/home/{}/Documents/ICT3211_BlueTeamPlatform/application".format(getpass.getuser())


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
