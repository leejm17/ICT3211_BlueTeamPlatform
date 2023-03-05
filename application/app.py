from flask import Flask, render_template, redirect, url_for, request

# Import Local Files
from main import initiate_ftp, windows_ftp_process, windows_ftp_automate, retrieve_cronjobs, action_cronjobs
from main import list_of_local_apps, retrieve_arkime_views
from admin import retrieve_glob_var, retrieve_arkime_var, retrieve_networkcapture_var, update_env
from forms import DataTransfer_Form, AdminConfig_DataTransfer_Form, AdminConfig_AppLaunch_Form#, AdminConfig_NetworkCapture_Form


# Create Flask App
app = Flask(__name__)
app.config.from_object('config.DevConfig')	# Using a development configuration
##app.config.from_object('config.ProdConfig')	# Using a production configuration


# App routes
@app.route("/", methods=["GET"], endpoint="home")
def home_page():
	return render_template("/home.html")


########## START Admin Config Pages ##########

@app.route("/admin", methods=["GET"], endpoint="admin")
def admin_page():
	return render_template("/admin/admin_config.html")


@app.route("/admin/data_transfer", methods=["GET", "POST"], endpoint="admin.data_transfer")
def admin_datatransfer_page():
	form = AdminConfig_DataTransfer_Form(request.form)
	if request.method == "POST":
		# Update .datatransfer with new values
		updated_configs = update_env("datatransfer", form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)

	return render_template("/admin/config_data_transfer.html", form=form)


@app.route("/admin/app_launch", methods=["GET", "POST"], endpoint="admin.app_launch")
def admin_applaunch_page():
	form = AdminConfig_AppLaunch_Form(request.form)
	if request.method == "POST":
		# Update .arkime with new values
		updated_configs = update_env("arkime", form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)

	return render_template("/admin/config_app_launch.html", form=form)


@app.route("/admin/honeypot", methods=["GET"], endpoint="admin.honeypot")
def admin_honeypot_page():
	return render_template("/admin/honeypot.html")


@app.route("/admin/spyder", methods=["GET"], endpoint="admin.spyder")
def admin_spyder_page():
	return render_template("/admin/spyder.html")


@app.route("/admin/machine_learning", methods=["GET"], endpoint="admin.machine_learning")
def admin_machinelearning_page():
	return render_template("/admin/machine_learning.html")


########## END Admin Config Pages ##########
########## START Data Transfer Pages ##########

@app.route("/data_transfer", methods=["GET"], endpoint="data_transfer")
def datatransfer_page():
	return render_template("/data_transfer/data_transfer.html")


@app.route("/data_transfer/smart_meter", methods=["GET", "POST"], endpoint="data_transfer.smart_meter")
def datatransfer_smartmeter_page():
	form = DataTransfer_Form(request.form)
	if request.method == "POST":
		if request.form:

			# Initiate FTP Process
			ftp_dir = ["SmartMeterData", "WiresharkData"]
			if request.form["submit"] in ftp_dir:
				success, dir_list = initiate_ftp(request.form["submit"])
				form.data_source.data = request.form["submit"]
				days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
				
				# If FTP Connection Established
				if success:
					return render_template("/data_transfer/smart_meter.html", ip=global_var()["windows_ip"], form=form, dir_list=dir_list, meters=dir_list, days_of_week=days_of_week)
				# Else FTP Connection NOT Established
				else:
					return render_template("/data_transfer/connection_failure.html", ip=global_var()["windows_ip"], message=dir_list)

			# Data Transfer Process
			else:
				# If Transfer Type is Now
				if form.transfer_type.data == "Now":
					# Perform Data Transfer Now
					success, message = windows_ftp_process(form)
					if success:
						return render_template("/data_transfer/smart_meter/download_success.html", message=message)
					else:
						return render_template("/data_transfer/smart_meter/download_failure.html", message=message)

				# Else Transfer Type is Scheduled
				else:
					# Schedule Data Transfer based on Form Data
					success, cron, job = windows_ftp_automate(form)
					if success:
						return render_template("/data_transfer/jobs/cronjob_success.html", cron_message=cron, job_message=job)
					else:
						return render_template("/data_transfer/jobs/cronjob_failure.html", cron_message=cron, job_message=job)

	return render_template("/data_transfer/smart_meter.html", ip=global_var()["windows_ip"], form=form)


@app.route("/data_transfer/network", methods=["GET", "POST"], endpoint="data_transfer.network")
def datatransfer_network_page():
	if request.method == "POST" and request.form["action"] == "browse":
		# Open Files application
		filepath = "{}/pcapFiles".format("/".join(app.config["APP_DIR"].split("/")[:-2]))
		subprocess.Popen(["xdg-open", filepath])
		#subprocess.Popen(["xdg-open", networkcapture_var()["capture_path"]])

	return render_template("/data_transfer/network_capture.html")


@app.route("/data_transfer/manage_jobs", methods=["GET", "POST"], endpoint="data_transfer.manage_jobs")
def datatransfer_managejobs_page():
	if request.method == "POST":
		if request.form["action"]:
			# Perform one of Action: Enable, Disable, Delete job
			action_cronjobs(request.form["action"])

	# Retrieve list of dictionary-per-job from CronTab
	return render_template("/data_transfer/manage_jobs.html", job_list=retrieve_cronjobs())


########## END Data Transfer Pages ##########
########## START App Launch Pages ##########

@app.route("/app_launch", methods=["GET"], endpoint="app_launch")
def applaunch_page():
	return render_template("/app_launch/app_launch.html")


@app.route("/app_launch/local_apps", methods=["GET", "POST"], endpoint="app_launch.local_apps")
def applaunch_localapps_page():
	# Retrieve list of user-installed local applications
	app_list = list_of_local_apps()
	button_style = ["info", "primary", "success", "danger", "warning"]

	if request.method == "POST":
		try:
			# Open local application
			subprocess.Popen([request.form["action"]])
		except Exception as e:
			# If local application does NOT exist
			print("Cannot find {}: {}".format(request.form["action"], e))
			return render_template("/app_launch/local_apps.html", message=request.form["action"], app_list=app_list, style=button_style)

	return render_template("/app_launch/local_apps.html", app_list=app_list, style=button_style)


@app.route("/app_launch/arkime", methods=["GET"], endpoint="app_launch.arkime")
def applaunch_arkimeviews_page():
	# Retrieve list of dictionary-per-view from Arkime /api/views
	success, views = retrieve_arkime_views()
	
	# If /api/views returns a valid list
	if success:
		arkime_views = {}
		for view in views:
			# Append each view's ID to their view's label
			arkime_views[view["name"]] = "https://{}/sessions?view={}".format(request.remote_addr, view["id"])

	# Else /api/views returns an error
	else:
		return render_template("/app_launch/arkime.html", arkime_views=views)

	button_style = ["info", "primary", "success", "danger", "warning"]
	return render_template("/app_launch/arkime.html", arkime_views=arkime_views, style=button_style)


########## END App Launch Pages ##########

@app.route("/help", methods=["GET"], endpoint="help")
def help_page():
	return render_template("/help.html")


########## START Variables ##########

@app.route("/global_var", methods=["GET"])
def global_var():
	return retrieve_glob_var()


@app.route("/arkime_var", methods=["GET"])
def arkime_var():
	return retrieve_arkime_var()


@app.route("/networkcapture_var", methods=["GET"])
def networkcapture_var():
	return retrieve_networkcapture_var()


########## END Variables ##########

if __name__ == "__main__":
	app.run(host=app.config["APP_IP"], port=app.config["APP_PORT"])
