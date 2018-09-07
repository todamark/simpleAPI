'''

'''

from simpleAPI.emailClient import EmailClient
from simpleAPI.apiParser import ApiParser
from threading import Thread
from queue import Queue
from time import sleep
import configparser
import sys

class Api:
	REFRESH_RATE_S = 0.1
	registered_callbacks = {}
	def __init__(self, api_dir = './apis', config_file = './config'):
		self.config_file = config_file
		self.email = EmailClient(config_file)
		self.api = ApiParser()
		if api_dir:
			self.api.load_apis_from_directory(api_dir)
		self.queues = {}
		self.verified_senders = []

	def auto(self, make_callbacks = True):
		self.email_thread = Thread(target=self.update_emails_looper, args = {self.REFRESH_RATE_S, make_callbacks}, daemon=True)
		self.email_thread.start()

	def update_emails_looper(self, refresh_rate_s, make_callbacks):
		while True:
			try:
				self.update_emails(make_callbacks)
				sleep(refresh_rate_s)
			except (KeyboardInterrupt, SystemExit):
				sys.exit(1)

	def update_emails(self, make_callbacks):
		try:
			emails = self.email.get_emails()
			for email in emails:
				if not self.check_verified_sender(email['sender']):
					print("Unverified sender " + email['sender'])
					continue
				parsed_call = self.api.parse_email(email['body'])
				if 'api_name' not in parsed_call or 'error' in parsed_call:
					print("Error: " + parsed_call['error'])
					continue
				api_name = parsed_call['api_name']
				if make_callbacks:
					self.make_callback(api_name, parsed_call)
				else:
					if api_name not in self.queues:
						self.queues[api_name] = Queue()
					self.queues[api_name].put(parsed_call)
		except (KeyboardInterrupt, SystemExit):
			sys.exit(1)

	def make_callback(self, api_call, parsed_call):
		if api_name not in self.registered_callbacks:
			raise Exception('No callback registered for ' + str(api_name))
		elif 'function_name' not in parsed_call:
			raise Exception('No function name defined in call')
		elif parsed_call['function_name'] not in registered_callbacks[api_name]:
			raise Exception('Function name ' + str(parsed_call['function_name']) + 'not registered')
		elif 'options' not in parsed_call:
			raise Exception('No options declared in call')
		else:
			func = mapping[parsed_call['function_name']]
			func(**parsed_call['options'])

	# Returns api calls from the queue, in the order they came
	# Returns only one api call, and blocks until one comes in if there are none currently or None if the api isn't known
	def get_api_call(self, api_name):
		if api_name not in self.queues:
			return None 
		try:
			return self.queues[api_name].get(block = True)
		except (KeyboardInterrupt, SystemExit):
			sys.exit(1)

	def register_api(self, api_name):
		if api_name not in self.queues:
			self.queues[api_name] = Queue()
			self.registered_callbacks[api_name] = {}

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

	def register_callback(self, api_name, function_name, callback):
		if api_name not in self.registered_callbacks:
			raise Exception('unregistered api: ' + str(api_name))
		self.registered_callbacks[api_name][function_name] = callback