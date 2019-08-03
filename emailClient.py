'''
Low-level email client to read emails and return raw data
Need the following configs in the given config file:
	email_address: the address to read emails from
	email_password: the password for that email address
	smtp_server: the smtp server for the email server, provided is for gmail
	smtp_port: the port of the smtp server, provided is for gmail
Recommended to create an entirely separate email from your normal one to avoid 
putting your general email password in plain text
'''

from io import StringIO
import configparser
import imaplib
import smtplib
from email import message_from_string
import re

ONLY_UNREAD = True

class EmailClient:
	def __init__(self, config_file='./config'):
		#---- READ CONFIGURATIONS IN ----#
		config = configparser.ConfigParser()
		config.read(config_file)
		if 'EMAIL' not in config:
			raise Exception('No email configuration provided')
		self.email_address = config['EMAIL']['email_address']
		if not self.email_address:
			raise Exception('No email address provided in configuration file')
		self.email_password = config['EMAIL']['email_password']
		if not self.email_password:
			raise Exception('No email password provided in configuration file')
		self.smtp_server = config['EMAIL']['smtp_server']
		if not self.smtp_server:
			raise Exception('No smtp server provided in configuration file')
		self.smtp_port = config['EMAIL']['smtp_port']
		if not self.smtp_port:
			raise Exception('No smtp port provided in configuration file')
		self.subject_identifier = config['EMAIL']['subject_identifier']
		if not self.smtp_port:
			raise Exception('No subject identifier provided in configuration file')
		#--------------------------------#
		self.mail = imaplib.IMAP4_SSL(self.smtp_server)
		self.mail.login(self.email_address, self.email_password)
		self.smtp = smtplib.SMTP_SSL(self.smtp_server)
		self.smtp.login(self.email_address, self.email_password)


	# Gets all unread emails from mailbox, and returns all that match the following criteria:
	#	- unread
	#	- subject line equals subject_identifier (by default, 'iot')
	# Returns the emails in a python list, from oldest to newest, in a dict with the following fields:
	# 	sender: the message sender (asdf@gmail.com)
	#	body: The body data in the email
	def get_emails(self):
		self.mail.select('inbox')
		result = []
		unseen_parameter = 'UNSEEN' if ONLY_UNREAD else None
		_, data = self.mail.search(None, 'SUBJECT', self.subject_identifier, unseen_parameter)
		mail_ids = data[0]
		id_list = mail_ids.split()
		for email_id in id_list:
			_, data = self.mail.fetch(email_id, '(RFC822)')
			for response_part in data:
				if isinstance(response_part, tuple):
					email_dict = {}
					msg = message_from_string(response_part[1].decode('utf-8'))
					# searches for email-shaped substring of the from field
					# usually comes like: "name namey <name@place.com>", but want to be flexible
					email_dict['sender'] = re.search(r'[\w\.-]+@[\w\.-]+', msg['from']).group(0)
					email_dict['body'] = msg.get_payload()[0].get_payload()
					result.append(email_dict)
		return result

	def send_email(self, email, body):
		self.smtp.sendmail(self.email_address, email, body)
