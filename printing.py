import sys

# Definitions
# Print critical error and exit
def printerr(s):
	print(s)
	sys.exit()


# Print only if not running in quiet mode
def qprint(s):
    if not quiet:
        print(s)


