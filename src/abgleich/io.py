# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CONSTANTS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# https://en.wikipedia.org/wiki/ANSI_escape_code
c = {
	'RESET': '\033[0;0m',
	'BOLD': '\033[;1m',
	'REVERSE': '\033[;7m',
	'GREY': '\033[1;30m',
	'RED': '\033[1;31m',
	'GREEN': '\033[1;32m',
	'YELLOW': '\033[1;33m',
	'BLUE': '\033[1;34m',
	'MAGENTA': '\033[1;35m',
	'CYAN': '\033[1;36m',
	'WHITE': '\033[1;37m'
	}


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def colorize(text, col):
	return c.get(col.upper(), c['GREY']) + text + c['RESET']

def humanize_size(size, add_color = False):

	suffix = 'B'

	for unit, color in (
		('', 'cyan'),
		('Ki', 'green'),
		('Mi', 'yellow'),
		('Gi', 'red'),
		('Ti', 'magenta'),
		('Pi', 'white'),
		('Ei', 'white'),
		('Zi', 'white'),
		('Yi', 'white')
		):
		if abs(size) < 1024.0:
			text = '%3.1f %s%s' % (size, unit, suffix)
			if add_color:
				text = colorize(text, color)
			return text
		size /= 1024.0

	raise ValueError('"size" too large')
