from wtforms import (
	Form,
	StringField,
	SelectMultipleField,
	RadioField,
	DateField,
	TimeField,
	IntegerField,
	SelectField,
	SubmitField,
	PasswordField
)
from wtforms.validators import (
	NumberRange,
	InputRequired,
	ValidationError
)
from flask_wtf import FlaskForm
from flask import flash
from datetime import datetime
import requests


########## START Data Transfer Forms ##########

"""Form for Smart Meter (Windows) Page"""
class DataTransfer_Form(Form):

	#### Transfer Type: Both Now & Schedule ####
	data_source = StringField(
		label="Data Source",
		validators=[
			InputRequired()],
		render_kw={"disabled": ""})

	meters = SelectMultipleField(
		label="Meters",
		validators=[
			InputRequired()])

	transfer_type = RadioField(
		label="Transfer Type",
		choices=["Now", "Schedule"],
		default="Now",
		validators=[
			InputRequired()],
		render_kw={"onclick": "toggle_transfer_type(this.id)"})

	start_time = TimeField(
		label="Data Start Time",
		format="%H:%M:%S",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()],
		render_kw={"step": "1", })


	#### Wireshark Data: WiresharkData only ####
	wireshark_source = RadioField(
		label="Wireshark Source",
		choices=["Ethernet", "WiFi"],
		default="Ethernet")


	#### Transfer Type: Now only ####
	date = DateField(
		label="Date",
		validators=[
			InputRequired()],
		default=datetime(2023, 1, 1))

	end_time = TimeField(
		label="Data End Time",
		format="%H:%M:%S",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()],
		render_kw={"step": "1"})


	#### Transfer Type: Schedule only ####
	timezone = SelectField(
		label="Timezone",
		choices=[
			"UTC +00",
			"GMT +01", "GMT +02", "GMT +03", "GMT +04", "GMT +05", "GMT +06", "GMT +07", "GMT +08", "GMT +09", "GMT +10", "GMT +11", "GMT +12",
			"GMT -01", "GMT -02", "GMT -03", "GMT -04", "GMT -05", "GMT -06", "GMT -07", "GMT -08", "GMT -09", "GMT -10", "GMT -11", "GMT -12"],
		default="GMT +08",
		validators=[
			InputRequired()])

	timezone_prefix = SelectField(
		label="Timezone",
		choices=["+", "-"],
		default="+",
		validators=[
			InputRequired()])

	timezone_value = SelectField(
		label="GMT",
		choices=[
			"00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
		default="08",
		validators=[
			InputRequired()])

	transfer_freq = RadioField(
		label="Transfer Frequency",
		choices=["Daily", "Weekly", "Monthly"],
		render_kw={"onclick": "toggle_transfer_freq(this.id)"})

	transfer_freq_time = TimeField(
		label="At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_freq_week = SelectMultipleField(
		label="on a",
		validators=[
			InputRequired()])
	transfer_freq_week_time = TimeField(
		label="At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_freq_month = IntegerField(
		label="on the",
		default=1,
		validators=[
			InputRequired(),
			NumberRange(min=1, max=31, message="Invalid day of month")],
		render_kw={"style": "width:50px; margin: 0px 5px 0px 0px"})
	transfer_freq_month_time = TimeField(
		label="At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_dur = SelectField(
		label="Data to Download",
		choices=[1, 5, 10, 15, 30],
		default=5,
		validators=[
			InputRequired()],
		render_kw={"style": "width:45px; margin: 0px 5px 0px 0px"})

	job_name = StringField(
		label="Job Name",
		default="New Job",
		validators=[
			InputRequired()],
		render_kw={"placeholder": "Enter a job name"})

	submit = SubmitField("Data Transfer", render_kw={"id": "div_btn"})


########## END Data Transfer Forms ##########
########## START Spider Forms ##########

"""Form for Spider Submit Job Page"""
def url_check(form, field):
	try:
		if requests.get(field.data).status_code != 200:
			raise
	except:
		message = "A valid HTTP/S link must be provided: {}".format(field.data)
		flash(message, "danger")
		raise ValidationError(message)
	if form.spiderChoice.data == "github" and "github.com" not in field.data:
		message = "A GitHub repository link must be provided"
		flash(message, "danger")
		raise ValidationError(message)
	elif form.spiderChoice.data == "stackoverflow" and "stackoverflow.com" not in field.data:
		message = "A valid StackOverFlow link must be provided"
		flash(message, "danger")
		raise ValidationError(message)

class Spider_Form(FlaskForm):

	url = StringField(
		label="Input URL:",
		validators=[
			InputRequired(),
			url_check])

	scrapingDepth = SelectField(
		label="Scraping Depth: ",
		choices=[("0", "0"), ("1", "1"), ("2", "2")])

	spiderChoice = SelectField(
		label="Spider: ",
		coerce=str,
		validators=[
			InputRequired()])

	submit = SubmitField(
		label="Submit URL")


########## END Spider Forms ##########
########## START Admin Forms ##########

"""Form for Admin Data Transfer Page"""
class AdminConfig_DataTransfer_Form(Form):

	windows_ip = StringField(
		"Windows IP",
		validators=[
			InputRequired()])

	debian_ip = StringField(
		"Debian IP",
		validators=[
			InputRequired()])

	ftp_user = StringField(
		"FTP User",
		validators=[
			InputRequired()])

	ftp_pw = PasswordField(
		"FTP Password",
		validators=[
			InputRequired()])

	cron_user = StringField(
		"Host Username",
		validators=[
			InputRequired()])

	workers = IntegerField(
		"Host Multi-thread Workers",
		validators=[
			InputRequired(),
			NumberRange(min=1, max=1000, message="Only a maximum of 1000 Workers can be set")])


"""Form for Admin App Launch Page"""
class AdminConfig_AppLaunch_Form(Form):
	arkime_user = StringField(
		"Arkime Username",
		validators=[
			InputRequired()])

	arkime_password = PasswordField(
		"Arkime Password",
		validators=[
			InputRequired()])


"""Form for Admin Network Capture Page"""
class AdminConfig_NetworkCapture_Form(Form):
	capture_path = StringField(
		"PCAP File Path",
		validators=[
			InputRequired()])


########## END Admin Forms ##########
