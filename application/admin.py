import os, dotenv, ast


########## START Global Variables ##########

def retrieve_glob_var():
	# Global Variables
	dotenv_file = dotenv.find_dotenv(".env")
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .env

	return {
		"windows_ip": os.environ["WINDOWS_IP"],
		"debian_ip": os.environ["DEBIAN_IP"],
		"ftp_user": os.environ["FTP_USER"],
		"ftp_pw": os.environ["FTP_PW"],
		"cron_user": os.environ["CRON_USER"],
		"app_list": os.environ["APP_LIST"]}


def retrieve_arkime_var():
	# Global Variables
	dotenv_file = dotenv.find_dotenv(".arkimefilter")
	dotenv.load_dotenv(dotenv_file, override=True)	# Take environment variables from .env

	return ast.literal_eval(os.environ["ARKIME_FILTERS"])


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
	dotenv_file = dotenv.find_dotenv(".env")
	dotenv.load_dotenv(dotenv_file)

	updated_configs = []
	# Write changes to .env file.
	for field in form:
		if field.data != os.environ[field.name.upper()]:
			updated_configs.append(field.label)
			dotenv.set_key(dotenv_file, field.name.upper(), field.data)

	return updated_configs


########### END Data Transfer Config ###########


########## START App Launch Config ##########
"""
def add_filter(form):
	dotenv_file = dotenv.find_dotenv(".arkimefilter")
	dotenv.load_dotenv(dotenv_file)

	update = False
	arkime_filters = retrieve_arkime_var()
	if form.new_filter_name.data not in arkime_filters:
		arkime_filters[form.new_filter_name.data] = form.new_filter_url.data
		dotenv.set_key(dotenv_file, "ARKIME_FILTERS", str(arkime_filters))
		update = True

	return update


def remove_filter(filter_name):
	dotenv_file = dotenv.find_dotenv(".arkimefilter")
	dotenv.load_dotenv(dotenv_file)

	arkime_filters = retrieve_arkime_var()
	del arkime_filters[filter_name]
	dotenv.set_key(dotenv_file, "ARKIME_FILTERS", str(arkime_filters))
	print(arkime_filters)
"""

########### END App Launch Config ###########
