from wtforms import (
	Form,
	StringField,
	SelectMultipleField,
	RadioField,
	DateField,
	TimeField,
	IntegerField,
	SelectField,
	SubmitField
)
from wtforms.validators import NumberRange, InputRequired
from datetime import datetime


"""Form for Smart Meter (Windows) Page"""
class DataTransfer_Form(Form):

	#### Transfer Type: Both Now & Schedule ####
	data_source = StringField(
		"Data Source",
		validators=[
			InputRequired()],
		render_kw={"disabled": ""})

	meters = SelectMultipleField(
		"Meters",
		validators=[
			InputRequired()])

	transfer_type = RadioField(
		"Transfer Type",
		choices=["Now", "Schedule"],
		default="Now",
		validators=[
			InputRequired()],
		render_kw={"onclick": "toggle_transfer_type(this.id)"})

	start_time = TimeField(
		"Data Start Time",
		format="%H:%M:%S",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()],
		render_kw={"step": "1", })


	#### Wireshark Data: WiresharkData only ####
	wireshark_source = RadioField(
		"Wireshark Source",
		choices=["Ethernet", "WiFi"],
		default="Ethernet")


	#### Transfer Type: Now only ####
	date = DateField(
		"Date",
		validators=[
			InputRequired()],
		default=datetime(2023, 1, 1))

	end_time = TimeField(
		"Data End Time",
		format="%H:%M:%S",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()],
		render_kw={"step": "1"})


	#### Transfer Type: Schedule only ####
	transfer_freq = RadioField(
		"Transfer Frequency",
		#choices=["Minute", "Hourly", "Daily", "Weekly", "Monthly"],
		choices=["Daily", "Weekly", "Monthly"],
		render_kw={"onclick": "toggle_transfer_freq(this.id)"})

	transfer_freq_time = TimeField(
		"At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_freq_week = SelectMultipleField(
		"on a",
		validators=[
			InputRequired()])
	transfer_freq_week_time = TimeField(
		"At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_freq_month = IntegerField(
		"on the",
		default=1,
		validators=[
			InputRequired(),
			NumberRange(min=1, max=31, message="Invalid day of month")],
		render_kw={"style": "width:50px; margin: 0px 5px 0px 0px"})
	transfer_freq_month_time = TimeField(
		"At",
		format="%H:%M",
		default=datetime(2023, 1, 1, hour=12),
		validators=[
			InputRequired()])

	transfer_dur = SelectField(
		"Data to Download",
		choices=[1, 5, 10, 15, 30],
		default=5,
		validators=[
			InputRequired()],
		render_kw={"style": "width:45px; margin: 0px 5px 0px 0px"})

	job_name = StringField(
		"Job Name",
		default="New Job",
		validators=[
			InputRequired()],
		render_kw={"placeholder": "Enter a job name"})

	submit = SubmitField("Data Transfer", render_kw={"id": "div_btn"})


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

	ftp_pw = StringField(
		"FTP Password",
		validators=[
			InputRequired()])

	cron_user = StringField(
		"Host Username",
		validators=[
			InputRequired()])


"""Form for Admin App Launch Page"""
class AdminConfig_AppLaunch_Form(Form):
	arkime_user = StringField(
		"Arkime Username",
		validators=[
			InputRequired()])

	arkime_password = StringField(
		"Arkime Password",
		validators=[
			InputRequired()])
