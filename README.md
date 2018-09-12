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

## Manual Access
controller.get_api_call(api_name) will return API calls to the requested api name in the order that they were received by the email address. If there is no new calls to this api, this function will block until there is one to get. These will come in the following python dict format:

	{
		"api_name": api_name
		"function_name": function_name
		"options": { "option1": "value" }
	}

## Api class
The controller class is the main way to set up your API server. Its functions are the following:
`Api(api_dir, config_file)`: the two parameters to the constructors are paths to the configuration files, by default api_dir = './apis' and config_file = './config'
`start()`: Once everything is configured, call this to keep the server running. Can be stopped by Keyboard Interrupt
`get_api_handler(api_name)`: Returns an ApiHandler which can be used to register callbacks to api functions
`get_api_call(api_name)`: Low level call to directly access api calls. Do not use in conjunction with an api handler for a given API. See documentation above

## ApiHandler Class
The easiest way to interact with your API is through registered callbacks in the ApiHandler class. To get an ApiHandler, call `get_api_handler(api_name)` on your configured controller object. This will return an object on which you can register API functions to callback functions, as seen in the example code snippet below. Once registered, the ApiHandler will automatically call your callback any time a registered api function is called. The only functions of this class are the following:
`register_callback(function_name, callback)`: Will call "callback" any time "function_name" is called through the api
`register_callbacks(mapping)`: takes a dict of function_names to callbacks, and bulk registers them

## Example code
```python
from simpleAPI import api

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

api = api.Api(api_dir = './apis', config_file = './config')
lights_handler = api.get_api_handler('lights')
lights_handler.register_callbacks(mapping)
api.start() # Keeps the main thread running so emails will continue being processed
```

./apis/lights_api.json
```
{"api_name":"lights", 
	"on":{},
	"change_color":{"required": ["color"]},
	"dim":{"optional":["amount"]},
	"off":{}
}
```