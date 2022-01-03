#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

"""

import os
import sys
from jinja2 import Environment, FileSystemLoader

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

print('Content-type: text/html\n')
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('help.html')
print(template.render(url=url))
