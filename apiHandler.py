from threading import Thread

class ApiHandler:
	registered_callbacks = {}

	def __init__(self, controller, api_name):
		self.api_name = api_name
		self.controller = controller
		self.start()

	def start(self):
		self.callback_thread = Thread(target=self.callback_looper, daemon=True)
		self.callback_thread.start()

	def callback_looper(self):
		while True:
			request = self.controller.get_api_call(self.api_name)
			function_name = request['function_name']
			if not function_name:
				print("Unknown function: " + str(function_name))
				continue
			func = self.registered_callbacks[function_name]
			t = Thread(target=self.callback_handler, args = (func, request['sender'], request['options']), daemon=True)
			t.start()

	def callback_handler(self, func, sender, kwargs):
		result = func(**kwargs)
		self.controller.return_api_response(result, sender)

	def register_callback(self, function_name, callback):
		self.registered_callbacks[function_name] = callback

	# Give me a dict in the following format to bulk-register:
	# {
	# "on": on,
	# "off": off,
	# "change_color": change_color,
	# "dim": dim
	# }	
	# where the values are functions
	def register_callbacks(self, callbacks):
		for function_name in callbacks:
			self.register_callback(function_name, callbacks[function_name])
