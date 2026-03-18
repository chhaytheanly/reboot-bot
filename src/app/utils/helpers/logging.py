import logging

# Define the color
GREEN = "\033[92m"
RED = "\033[91m"
END = "\033[0m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message: str):
        self.logger.info(f"{GREEN}{message}{END}")

    def warning(self, message: str):
        self.logger.warning(f"{YELLOW}{message}{END}")

    def error(self, message: str):
        self.logger.error(f"{RED}{message}{END}")

    def debug(self, message: str):
        self.logger.debug(f"{CYAN}{message}{END}")
        
logger = Logger(__name__)