'''
Parser for Email-based APIs
Emails subscribing to an api should have their body formatted in the following way:
	api_name \r\n
	function_name \r\n
	option1=xxx \r\n
	option2=xxx \r\n 
	optionX=xxx
Essentially this class does parsing from raw-string email, checks for validity, and 
returns cleaned, easy-to-use results
'''

import json
from os import listdir
from os.path import isfile, join

class ApiParser:
	def __init__(self):
		self.apis = {}

	# Provide the parser with a new api to parse
	# api should be a dict formatted as follows:
	# {
	# api_name: music,
	# function1: { required: [option1, option2], optional: [option3] },
	# function2: { required: [option1], optional: [option2] }
	# }
	def load_api(self, api):
		if 'api_name' not in api:
			raise Exception('Must proivide api_name')
		for key in api:
			if key != 'api_name':
				if 'required' not in api[key]:
					api[key]['required'] = []
				if 'optional' not in api[key]:
					api[key]['optional'] = []
		self.apis[api['api_name']] = api

	def load_api_from_json(self, file):
		with open(file, 'r') as f:
			api = json.load(f)
			self.load_api(api)

	def load_apis_from_directory(self, api_dir):
		files = [f for f in listdir(api_dir) if isfile(join(api_dir, f))]
		for file in files:
			self.load_api_from_json(join(api_dir, file))

	def get_apis(self):
		return self.apis.keys()

	# Parses the given email using previously loaded APIs
	# If the email doesn't adhere to any loaded API, throws exception
	# 	Non-adherence is defined by: unknown api_name, unknown_function
	# Return format looks like the following:
	#{
	#	api_name: music,
	#	function: asdf,
	#	options: {
	#		option1: asdf
	#		option2: asdf
	#	}
	#}
	# If invalid email for any given reason, the result will have 'error' field with explanation

	def parse_email(self, email):
		result = {}
		lines = email.split('\r\n')
		if len(lines) < 2:
			result['error'] = 'Only ' + len(lines) + ' given, need at least 2'
			return result
		api_name = lines[0]
		if api_name not in self.apis:
			result['error'] = 'Invalid API Name given: ' + str(api_name)
			return result
		api = self.apis[api_name]
		function_name = lines[1]
		if function_name not in api:
			result['error'] = 'Invalid function name: ' + str(function_name)
			return result
		required = api[function_name]['required']
		optional = api[function_name]['optional']
		result['options'] = {}
		for line in lines[2:]:
			if len(line) == 0:
				continue
			key, value = line.split('=')
			if key in required:
				required.remove(key)
			if key in optional:
				optional.remove(key)
			result['options'][key] = value
		if len(required) != 0:
			result['error'] = 'missing required options: ' + str(required)
		result['api_name'] = api_name
		result['function_name'] = function_name
		return result