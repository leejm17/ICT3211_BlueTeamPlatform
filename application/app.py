from flask import Flask, render_template, redirect, url_for, request
import os, subprocess

# Import Local Files
from main import initiate_ftp, windows_ftp_process, windows_ftp_automate, retrieve_cronjobs, action_cronjobs
from admin import retrieve_glob_var, update_env
from forms import DataTransfer_Form, AdminConfig_Form


# Create Flask App
app = Flask(__name__)


# App routes
@app.route("/", methods=["GET"], endpoint="home")
def home_page():
	return render_template("/home.html")


@app.route("/admin", methods=["GET"], endpoint="admin")
def admin_page():
	return render_template("/admin/admin_config.html")


@app.route("/admin/honeypot", methods=["GET"], endpoint="honeypot")
def admin_honeypot_page():
	return render_template("/admin/honeypot.html")


@app.route("/admin/spyder", methods=["GET"], endpoint="spyder")
def admin_spyder_page():
	return render_template("/admin/spyder.html")


@app.route("/admin/data_transfer", methods=["GET", "POST"], endpoint="admin.data_transfer")
def admin_datatransfer_page():
	form = AdminConfig_Form(request.form)
	if request.method == "POST":
		updated_configs = update_env(form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)
	return render_template("/admin/data_transfer.html", form=form)


@app.route("/global_var", methods=["GET"])
def global_var():
	glob_dict = retrieve_glob_var()
	return glob_dict


@app.route("/admin/machine_learning", methods=["GET"], endpoint="machine_learning")
def admin_machinelearning_page():
	return render_template("/admin/machine_learning.html")


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
				global_dict = retrieve_glob_var()
				if success:
					return render_template("/data_transfer/smart_meter.html", ip=global_dict["windows_ip"], form=form, dir_list=dir_list, meters=dir_list, days_of_week=days_of_week)
				else:
					return render_template("/data_transfer/connection_failure.html", ip=global_dict["windows_ip"], message=dir_list)

			# Data Transfer Process
			else:
				if form.transfer_type.data == "Now":
					success, message = windows_ftp_process(form)
					if success:
						return render_template("/data_transfer/download_success.html", message=message)
					else:
						return render_template("/data_transfer/download_failure.html", message=message)

				else: # Schedule the Data Transfer for automation
					success, cron, job = windows_ftp_automate(form)
					if success:
						return render_template("/data_transfer/cronjob_success.html", cron_message=cron, job_message=job)
					else:
						return render_template("/data_transfer/cronjob_failure.html", cron_message=cron, job_message=job)

	global_dict = retrieve_glob_var()
	return render_template("/data_transfer/smart_meter.html", ip=global_dict["windows_ip"], form=form)


@app.route("/data_transfer/network", methods=["GET", "POST"], endpoint="data_transfer.network")
def datatransfer_network_page():
	if request.method == "POST" and request.form["action"] == "browse":
		filepath = "{}/FTP_Downloads".format("/".join(os.getcwd().split("/")[:-2]))
		subprocess.Popen(["xdg-open", filepath])
	return render_template("/data_transfer/network_capture.html")


@app.route("/data_transfer/manage_jobs", methods=["GET", "POST"], endpoint="data_transfer.manage_jobs")
def datatransfer_managejobs_page():
	if request.method == "POST":
		if request.form["action"]:
			action_cronjobs(request.form["action"])	# Action: Enable, Disable, Delete job

	# Retrieve list of dictionary-per-job from CronTab
	cron_jobs = retrieve_cronjobs()
	print(cron_jobs)
	return render_template("/data_transfer/manage_jobs.html", job_list=cron_jobs)


@app.route("/app_launch", methods=["GET"], endpoint="app_launch")
def applaunch_page():
	return render_template("/app_launch.html")


@app.route("/help", methods=["GET"], endpoint="help")
def help_page():
	return render_template("/help.html")
