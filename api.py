'''

'''

from simpleAPI.emailClient import EmailClient
from simpleAPI.apiParser import ApiParser
from simpleAPI.apiHandler import ApiHandler
from threading import Thread
from queue import Queue
from time import sleep
import configparser
import sys

class Api:
	auto_running = False

	def __init__(self, api_dir = './apis', config_file = './config'):
		self.config_file = config_file
		self.email = EmailClient(config_file)
		self.api = ApiParser()
		if api_dir:
			self.api.load_apis_from_directory(api_dir)
		self.queues = {}
		self.verified_senders = []
		self.register_all_apis()
		self.register_verified_senders()
		self.auto()

	def auto(self, refresh_rate_s = 0.1):
		if self.auto_running:
			return
		else:
			self.auto_running = True
		self.email_thread = Thread(target=self.update_emails_looper, args = {refresh_rate_s}, daemon=True)
		self.email_thread.start()

	# Just keeps the main thread alive so the daemons can do their work
	def start(self):
		while True:
			pass

	def update_emails_looper(self, refresh_rate_s):
		while True:
			try:
				self.update_emails()
				sleep(refresh_rate_s)
			except (KeyboardInterrupt, SystemExit):
				sys.exit(1)

	def update_emails(self):
		try:
			emails = self.email.get_emails()
			for email in emails:
				if not self.check_verified_sender(email['sender']):
					print("Unverified sender " + email['sender'])
					continue
				parsed_call = self.api.parse_email(email['body'])
				parsed_call['sender'] = email['sender']
				if 'api_name' not in parsed_call or 'error' in parsed_call:
					print("Error: " + parsed_call['error'])
					continue
				api_name = parsed_call['api_name']
				if api_name not in self.queues:
					self.queues[api_name] = Queue()
				self.queues[api_name].put(parsed_call)
		except (KeyboardInterrupt, SystemExit):
			sys.exit(1)

	def get_api_handler(self, api_name):
		if api_name not in self.queues:
			raise Exception('Unkonwn api name: ' + str(api_name))
		return ApiHandler(self, api_name)

	# Returns api calls from the queue, in the order they came
	# Returns only one api call, and blocks until one comes in if there are none currently or None if the api isn't known
	def get_api_call(self, api_name):
		if api_name not in self.queues:
			return None
		try:
			return self.queues[api_name].get(block = True)
		except (KeyboardInterrupt, SystemExit):
			sys.exit(1)

	def return_api_response(self, response, function_name, email):
		self.email.send_email(email, function_name, response)

	def register_api(self, api_name):
		if api_name not in self.queues:
			self.queues[api_name] = Queue()

	def register_all_apis(self):
		for api in self.api.get_apis():
			self.register_api(api)

	def register_verified_sender(self, sender):
		self.verified_senders.append(sender)

	def register_verified_senders(self):
		config = configparser.ConfigParser()
		config.read(self.config_file)
		verified_senders = config['EMAIL']['verified_emails']
		senders = verified_senders.split(',')
		for sender in senders:
			self.register_verified_sender(sender)

	def check_verified_sender(self, sender):
		return sender in self.verified_senders
