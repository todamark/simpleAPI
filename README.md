# simpleAPI

Simple Python messaging library meant for developing home IOT APIs without the need for third party services such as AWS Lambda. 

The system is all managed by a controller, which reads in emails from a configured IMAP account and puts resulting API calls onto a synchronized, blocking queue that can be read from the client with controller.get_api_call(api_name)

## API Definitions
APIs are defined in a folder, from which the controller reads all available files. They are each defined in JSON files in the following format:

	{
		"api_name": "",
		"function1_name": {"required": [], "optional": []},
		"function2_name": {},
		...
	}
Each function can list required and optional parameters, which will be checked by the API parser. If any required parameters are not given, the api will return an error. 

## Configuration
The controller also needs a config file in the following format: 

	[EMAIL]
	email_address = asdf@asdf.com
	email_password = password
	smtp_server = imap.gmail.com # or whatever SMTP server
	smtp_port = 993 # Or whatever SMTP port
	subject_identifier = 'iot' # this must be the subject of every email that you want to be taken as an API call
	verified_emails = asdf@asdf.com,ddd@ddd.com # only emails from these addresses will be taken as API calls

## Email Format
Emails must be formatted in the following way:

	from: a verified email
	subject: subject_identifier
	body:
		api_name
		function_name
		option1=value
		option2=value
		...
		optionx=value
Note that the body is composed of items with a new line separating each one. 

## Return Format
controller.get_api_call(api_name) will return API calls to the requested api name in the order that they were received by the email address. If there is no new calls to this api, this function will block until there is one to get. These will come in the following python dict format:

	{
		"api_name": api_name
		"function_name": function_name
		"options": { "option1": "value" }
	}

## Example code
```python
	from simpleIOT import controller

	def on():
		print("TURNED THE LIGHTS ON")

	def off():
		print("TURNED THE LIGHTS OFF")

	def change_color(color):
		print("CHANGED THE LIGHTS TO " + str(color))

	def dim(amount=10):
		print("DIMMED THE LIGHTS BY " + str(amount) + " PERCENT")

	mapping = {
		"on": on,
		"off": off,
		"change_color": change_color,
		"dim": dim
	}

	controller = controller.Controller(api_dir = './apis', config_file = './config')
	controller.register_verified_senders()
	controller.register_all_apis()
	controller.auto()
	while True:
		request = controller.get_api_call('lights')
		func = mapping[request['function_name']]
		func(**request['options'])
```