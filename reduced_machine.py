import RPi.GPIO as GPIO
import time, os.path, sys
import toml, argparse

parser = argparse.ArgumentParser(description="Communicate with the Mark 1 FPGA")
parser.add_argument("config_path")

args = parser.parse_args()

# Print critical error and exit
def printerr(s):
	print(s)
	sys.exit()

# Load config
if not os.path.isfile(config_path):
	printerr("ERROR: path " + args.config_path + " does not exist!")

try:
	with open(args.config_path, 'r') as f:
		config = toml.loads(f.read())
except Exception:
	printerr("ERROR: could not load config file. Perhaps invalid format?")


# Returns the pin number of given name
def getpin(s):
	try:
		keys = config["toFPGA"].keys() + config["fromFPGA"].keys()	
	except Exception:


# Set GPIO pins up
if config["pi_board_mode"] == "BOARD":
	GPIO.setmode(GPIO.BOARD)
elif config["pi_board_mode"] == "BCM":
	GPIO.setmode(GPIO.BCM)
else:
	printerr("ERROR: invalid pi_board_mode in " + args.config_path + " : " + config["pi_board_mode"])
	

GPIO.setwarnings(False)

# Set up output pins
for name, v in config["pins"]["fromFPGA"].iteritems():
	try:
		GPIO.setup(int(v[0]), GPIO.IN)
	except Exception:
		printerr("Error setting up fromFPGA pin" + name + ", " + str(v[0]))

# Set up input pins
for name, v in config["pins"]["toFPGA"].iteritems():
	try:
		GPIO.setup(int(v[0]), GPIO.OUT)
	except Exception:
		printerr("Error setting up toFPGA pin" + name + ", " + str(v[0]))


b = True
while True:
	GPIO.output(22, b)
	b = not b
	time.sleep(0.5)
