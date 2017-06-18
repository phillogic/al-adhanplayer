import logging
import os.path
import sys
# Set up gobal logging 

import logging
from logging import handlers

if not os.path.exists("logs"):
	os.makedirs("logs")
	print("Logs directory has been created")
# set up logging to file - see previous section for more details
#logging.basicConfig(level=logging.DEBUG,
 #                   format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
 #                   datefmt='%m-%d %H:%M',
 #                   filename='logs/run.log',
 #                   filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr

formatter = logging.Formatter("%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s",datefmt='%m-%d %H:%M:%S')


# set a format or console use
# tell the handler to use this format
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
# adding rotating file logger
rfh = handlers.RotatingFileHandler('logs/run.log', mode='a', maxBytes=1000000, backupCount=2, encoding=None, delay=0)
rfh.setFormatter(formatter)
logging.getLogger('').addHandler(rfh)
# set debug level for file
logging.getLogger('').setLevel(logging.DEBUG)
# Now, we can log to the root logger, or any other logger. First the root...
logging.info('Initialzing logging..')

# Now, define a couple of other loggers which might represent areas in your
# application:
