import RPi.GPIO as GPIO
import time, os.path, sys
import toml, argparse
import mark_1_comm
from printing import *
import urwid
import math
import turing_encoder
	


# Parse command line arguments
parser = argparse.ArgumentParser(description="Communicate with the Mark 1 FPGA")
parser.add_argument("config_path")
parser.add_argument("-q", help="Run in quiet mode", action="store_true")

args = parser.parse_args()

quiet = args.q



# Load config
if not os.path.isfile(args.config_path):
	printerr("ERROR: path " + args.config_path + " does not exist!")

# Raise error if fails
with open(args.config_path, 'r') as f:
	config = toml.loads(f.read())


# Create interface class
mark_1 = mark_1_comm.Mark1Comm(config)
mark_1.start_output_listening()

# Global variables
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

turing = turing_encoder.TuringEncoder(symbol_table)

# Print on screen stuff
def tube_to_text(tube):
	text = ""
	
	if display_type == "CRT":
		for i in range(math.floor(len(tube)/2)):
			for j in range(mark_1.LINE_LENGTH):
				if tube[2*i][j] and tube[2*i+1][j]:
					text = text + ":"
				elif tube[2*i][j]:
					text = text + "·"  # could be ˑ
				elif tube[2*i+1][j]:
					text = text + "."
				else:
					text = text + "-"
			text = text + "\n"

		# Deal with final line
		if len(tube)%2 != 0:
			for j in range(mark_1.LINE_LENGTH):
				if tube[-1][j]:
					text = text + "·"
				else:
					text = text + "-"
			text = text + "\n"
	
	else:	# display_type = "Turing"
		alternate = False
		for line in tube:
			text = text + turing.bin_to_turing(line)
			if alternate:
				text = text + "\n"
			else:
				text = text + " "
			alternate = not alternate

	return text

def update_display_tubes():
	data = mark_1.DISP
	for i in range(mark_1.S_TUBES):
		display_tubes[i].set_text(tube_to_text(data[i]))

def update_stop_lamp():
	#test_text.set_text(str(mark_1.SL))
	stop_lamp.set_state(mark_1.SL)

def output_CLK(checkbox, newstate):
	mark_1.output_by_name("TEST", newstate)

class Keyboard(urwid.Edit):
	def output_TPR(self, text):
		# decode text by writing Turing decode function
		binary = turing.turing_to_bin(text)
		if binary == None:
			printerr("ERROR: invalid string!")
		else:
			mark_1.output_TPR(binary)

	def keypress(self, size, key):
		if key == 'enter' and len(self.edit_text) == 8:
			self.output_TPR(self.edit_text)
			self.edit_text = ""
		if len(self.edit_text) < 8 or key == 'backspace':
			super().keypress(size, key)


# Create storage tubes
#display_tubes = [urwid.Text("Display tube" for i in range(mark_1.S_TUBES))]
display_tubes = [urwid.Text("Hello world from tube " + str(i)) for i in range(mark_1.S_TUBES)]
display_tubes_cols = urwid.Columns(display_tubes)

# Create typewriter

# Create switches
stop_lamp = urwid.CheckBox("stop_lamp")
display_lamps_cols = urwid.Columns([stop_lamp])
display = urwid.Pile([display_tubes_cols, display_lamps_cols])

# Create input buttons
manual_clock = urwid.CheckBox("manual_clock", on_state_change=lambda x, newstate : mark_1.output_by_name("CLK", newstate))
typewriter = Keyboard()

# Create input footer

test_text = urwid.Text("This is the footer")
footer_widgets = [test_text, manual_clock, typewriter]
footer = urwid.ListBox(urwid.SimpleFocusListWalker(footer_widgets))

# Render main screen
#fill = urwid.Frame(urwid.Filler(display_tubes_pile, 'top'), footer=footer)
fill = urwid.Frame(footer, header=display, focus_part='body')
loop = urwid.MainLoop(fill)

update_display_tubes()
mark_1.disp_callback = update_display_tubes
mark_1.sl_callback = update_stop_lamp

loop.run()


# Tests
#b = False

#mark_1.update_DISP()
#mark_1.update_SL()

#for i in range (11):
#	mark_1.output_by_name("SS", b)
#	b = not b
#	time.sleep(0.5)
