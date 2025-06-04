import logging
import os

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'program.log')

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('EnspireProgram')
