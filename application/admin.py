import os, dotenv


########## START Global Variables ##########

def retrieve_glob_var():
	# Global Variables
	dotenv_file = dotenv.find_dotenv()
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .env

	return {
		"windows_ip": os.environ["WINDOWS_IP"],
		"debian_ip": os.environ["DEBIAN_IP"],
		"ftp_user": os.environ["FTP_USER"],
		"ftp_pw": os.environ["FTP_PW"],
		"cron_user": os.environ["CRON_USER"],
		"app_list": os.environ["APP_LIST"]}


########### END Global Variables ###########


########## START Honeypot Config ##########
# Code Here
########### END Honeypot Config ###########


########## START Spyder Config ##########
# Code Here
########### END Spyder Config ###########


########## START Data Transfer Config ##########

# Source: https://stackoverflow.com/questions/63837315/change-environment-variables-saved-in-env-file-with-python-and-dotenv
def update_env(form):
	dotenv_file = dotenv.find_dotenv()
	dotenv.load_dotenv(dotenv_file)

	updated_configs = []
	# Write changes to .env file.
	for field in form:
		if field.data != os.environ[field.name.upper()]:
			updated_configs.append(field.label)
			dotenv.set_key(dotenv_file, field.name.upper(), field.data)

	return updated_configs

########### END Data Transfer Config ###########


########## START Machine Learning Config ##########
# Code Here
########### END Machine Learning Config ###########
