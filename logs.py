import logging

logging.basicConfig(filename='migrate.log',level=logging.INFO, format='%(levelname)s:%(name)s %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger("test")