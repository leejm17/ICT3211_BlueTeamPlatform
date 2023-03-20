import os, dotenv

########## START Global Variables ##########

"""Data Transfer Variables"""
def retrieve_glob_var():
	dotenv_file = dotenv.find_dotenv(".datatransfer")
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .datatransfer

	return {
		"windows_ip": os.environ["WINDOWS_IP"],
		"debian_ip": os.environ["DEBIAN_IP"],
		"ftp_user": os.environ["FTP_USER"],
		"ftp_pw": os.environ["FTP_PW"],
		"cron_user": os.environ["CRON_USER"],
		"workers": os.environ["WORKERS"]}


"""Arkime Variables"""
def retrieve_arkime_var():
	dotenv_file = dotenv.find_dotenv(".arkime")
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .arkime

	return {
		"arkime_user": os.environ["ARKIME_USER"],
		"arkime_password": os.environ["ARKIME_PASSWORD"]}


"""Network Capture Variables"""
def retrieve_networkcapture_var():
	dotenv_file = dotenv.find_dotenv(".networkcapture")
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .networkcapture

	return {
		"capture_path": os.environ["CAPTURE_PATH"]}


"""Database Variables"""
def retrieve_database_var():
	dotenv_file = dotenv.find_dotenv(".database")
	dotenv.load_dotenv(dotenv_file, override=False)	# Take environment variables from .database

	return {
		"db_host": os.environ["DB_HOST"],
		"database_db": os.environ["DATABASE_DB"],
		"db_user": os.environ["DB_USER"],
		"db_pwd": os.environ["DB_PWD"],
		"secret": os.environ["SECRET_KEY"]}


########## END Global Variables ##########
########## START .datatransfer / .arkime / .networkcapture Config ##########

"""Update Specified Environment File (or .env)"""
# Source: https://stackoverflow.com/questions/63837315/change-environment-variables-saved-in-env-file-with-python-and-dotenv
def update_env(env, form):
	# Load .env file
	dotenv_file = dotenv.find_dotenv(".{}".format(env))
	dotenv.load_dotenv(dotenv_file)

	updated_configs = []
	# Write changes to .env file
	for field in form:
		field.data = str(field.data)
		if field.data != os.environ[field.name.upper()]:
			updated_configs.append(field.label)
			dotenv.set_key(dotenv_file, field.name.upper(), field.data)

	# Return list of variables that were updated
	return updated_configs


########## END .datatransfer / .arkime / .networkcapture Config ##########
########## START Spider Config ##########
# Code Here
########## END Spider Config ##########
