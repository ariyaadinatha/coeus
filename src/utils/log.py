# used to setup to get log info and error
import logging

logging.basicConfig(filename='log/coeus.log',
    format='[%(asctime)s-%(levelname)s-%(funcName)s-%(lineno)d]: %(message)s', level=logging.INFO)
logger = logging.getLogger("coeus")