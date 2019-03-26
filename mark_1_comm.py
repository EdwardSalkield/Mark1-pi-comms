import RPi.GPIO as GPIO
import time, os.path, sys
from printing import printerr
import math

# Flatten list of lists
def flatten_index(ll, i):
	return [sublist[i] for sublist in ll]
	

class Mark1Comm:
	pi_board_mode = None
	pins_out = {}
	pins_in = {}
	LINE_LENGTH = None
	WORD_LENGTH = None
	PAGE_SIZE = None
	PAGES_PER_TUBE = None
	S_TUBES = None

	# State of the serial connections
	#  Inputs
	TPR_counter = 0		# 0 <= TPR_counter < LINE_LENGTH
	S_counter = 0		# 0 <= S_counter < WORD_LENGTH
	S = []
	TPR = []

	#  Outputs
	DISP_counter = 0	# 0 <= DISP_counter < PAGES_PER_TUBE * PAGE_SIZE * LINE_LENGTH
	DISP = [[]]
	SL = 1

	# Callbacks for output changes
	disp_callback = None
	sl_callback = None

	# Initialise configuration file on instantiation
	def __init__(self, config, disp_callback=None, sl_callback=None):
		if not isinstance(config, dict):
			printerr("ERROR: config of invalid type")

		try:
			self.pi_board_mode = config["pins"]["pi_board_mode"]
		except Exception:
			printerr("ERROR: no pi_board_mode in config file.")

		try:
			self.LINE_LENGTH = config["constants"]["LINE_LENGTH"]
		except Exception:
			printerr("ERROR: no LINE_LENGTH in config file.")

		try:
			self.WORD_LENGTH = config["constants"]["WORD_LENGTH"]
		except Exception:
			printerr("ERROR: no WORD_LENGTH in config file.")

		try:
			self.PAGE_SIZE = config["constants"]["PAGE_SIZE"]
		except Exception:
			printerr("ERROR: no PAGE_SIZE in config file.")

		try:
			self.PAGES_PER_TUBE = config["constants"]["PAGES_PER_TUBE"]
		except Exception:
			printerr("ERROR: no PAGES_PER_TUBE in config file.")

		try:
			self.S_TUBES = config["constants"]["S_TUBES"]
		except Exception:
			printerr("ERROR: no S_TUBES in config file.")


		self.S = [[0] for i in range(self.WORD_LENGTH)]
		self.TPR = [[0] for i in range(self.LINE_LENGTH)]
		self.DISP = [[[0] * self.LINE_LENGTH for i in range(self.PAGE_SIZE * self.PAGES_PER_TUBE)] for j in range(self.S_TUBES)]

		self.disp_callback = disp_callback
		self.sl_callback = sl_callback
		
		self.pins_out = dict([(name, flatten_index(sublist, 0)) for (name, sublist) in config["pins"]["toFPGA"].items()])
		self.pins_in = dict([(name, flatten_index(sublist, 0)) for (name, sublist) in config["pins"]["fromFPGA"].items()])

		self.GPIO_setup()
		#self.start_output_listening()
	
	
	# Set up GPIO pins
	def GPIO_setup(self):
		if self.pi_board_mode == "BOARD":
			GPIO.setmode(GPIO.BOARD)
		else:
			GPIO.setmode(GPIO.BCM)

		print("Board mode set to " + self.pi_board_mode)
		GPIO.setwarnings(False)
		
 
		# Set up IO pins
		for name, pin in self.pins_out.items():
			for p in pin:
				GPIO.setup(p, GPIO.OUT)
				print("Set up pin " + name + ", " + str(p))

		for name, pin in self.pins_in.items():
			for p in pin:
				GPIO.setup(p, GPIO.IN)
				print("Set up pin " + name + ", " + str(p))



	# Returns the pin number of given name
	def get_pin_by_name(self, name, isinput):
		#try:
		if isinput:
			return [int(n) for n in self.pins_in[name]]
		else:
			return [int(n) for n in self.pins_out[name]]
		#except Exception:
		#	printerr("ERROR: could not find pin " + name)


	# Input by name
	def input_by_name(self, name):
		return [GPIO.input(pin) for pin in self.get_pin_by_name(name, True)]

	# Output by name
	def output_by_name(self, namelist, state):
		if isinstance(namelist, list):
			pins = [self.get_pin_by_name(name, False) for name in namelist]
		else:
			pins = self.get_pin_by_name(namelist, False)
		return GPIO.output(pins, state)



	# Update the display tubes on DISP_CLK rise
	def update_DISP(self, channel):
		# Get the new data from the display tubes
		data = self.input_by_name("DISP_DATA")

		col = self.DISP_counter % self.LINE_LENGTH
		row = math.floor(self.DISP_counter / self.LINE_LENGTH)

		for i in range(self.S_TUBES):
			self.DISP[i][row][col] = data[i]

		self.DISP_counter += 1
		self.DISP_counter = self.DISP_counter % (self.LINE_LENGTH * self.PAGE_SIZE * self.PAGES_PER_TUBE)
		if self.disp_callback != None:
			self.disp_callback()


	# Update stop light
	def update_SL(self, channel):
		self.SL =  self.input_by_name("SL")[0]
		if self.sl_callback != None:
			self.sl_callback()

	def output_TPR(self, bits):
		for i in range(self.LINE_LENGTH):
			self.output_by_name("TPR_DATA", bits[i])
			self.output_by_name("TPR_CLK", True)

			# Split off thread to handle return value
			time.sleep(0.1)
			self.output_by_name("TPR_CLK", False)
			time.sleep(0.1)

	
	def start_output_listening(self):
		# Call update functions on pin change
		GPIO.add_event_detect(self.get_pin_by_name("DISP_CLK", True)[0], GPIO.RISING, callback=self.update_DISP)
		GPIO.add_event_detect(self.get_pin_by_name("SL", True)[0], GPIO.BOTH, callback=self.update_SL)
