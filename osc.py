import RPi.GPIO as GPIO
import time, os.path, sys
import toml, argparse, pickle
import mark_1_comm
from printing import *
import math
	


# Parse command line arguments
parser = argparse.ArgumentParser(description="Communicate with the Mark 1 FPGA")
parser.add_argument("config_path")
parser.add_argument("setup_path")
parser.add_argument("output_path")
parser.add_argument("-q", help="Run in quiet mode", action="store_true")

args = parser.parse_args()

quiet = args.q



# Load configs
if not os.path.isfile(args.config_path):
	printerr("error: path " + args.config_path + " does not exist!")
if not os.path.isfile(args.setup_path):
	printerr("error: path " + args.setup_path + " does not exist!")

# Raise error if fails
with open(args.config_path, 'r') as f:
	config = toml.loads(f.read())
with open(args.setup_path, 'r') as f:
	setup = toml.loads(f.read())

# Parse config file
mark_1 = mark_1_comm.Mark1Comm(config)

try:
	display_type = config["display_properties"]["display_type"]	# CRT, Turing
except Exception:
	printerr("ERROR: no [display_properties] display_type in " + args.config_path)

if display_type not in ["CRT", "Turing"]:
	printerr("ERROR: invalid [display_properties] display_type: " + str(display_type))

try:
	symbol_table = config["symbol_table"]
except Exception:
	printerr("ERROR: no [symbol_table] in " + args.config_path)

# Parse setup file
cycles = setup["cycles"]
n_OSC = setup["n_OSC"]
OSC = setup["OSC"]

#  Sanity check
assert(n_OSC == len(OSC))

real_cycles = cycles*(n_OSC+1)


data = [[] for i in range(n_OSC)]
# Run simulation
CLK = False
mark_1.output_by_name("CLK", CLK)
rawdata = ""

for cycle in range(cycles):
	for w_CLK in [1,0]:
		for i in range(n_OSC+1):
			# Send clock pulse
			for signal in [0,1]:
				mark_1.output_by_name("CLK", signal)
				time.sleep(0.0001)
			# Measure
			if i != 0:
				rawdata += str(mark_1.input_by_name("OSC")[0])
				data[(i-1)%n_OSC].append(mark_1.input_by_name("OSC")[0])
			



# Parse and output data
with open(args.output_path, 'wb') as f:
	pickle.dump(data, f)

print(data)
print(rawdata)
