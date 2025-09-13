import os
import yaml
import zipfile
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init

date = datetime.datetime.now().strftime("%d-%m-%Y")
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(f"log-{date}.log")

config = os.path.join("config", "config.yml")
with open(config, "r", encoding="utf-8") as yml:
    config = yaml.safe_load(yml)
    
DEBUG_MODE = config["debug"]["debug"]

init()

class Zipfilelog(TimedRotatingFileHandler):
    def rotate(self, source, dest):
        zip_name = dest + ".zip"
        
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(source, os.path.basename(source))
        os.remove(source)
        
handler = Zipfilelog(
    filename= os.path.join(log_dir, log_file),
    when="midnight",
    backupCount=7,
    encoding="utf-8"
)

handler.suffix = "%d-%m-%Y"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


class log:
    def log_event (message, end="\n", flush=False, shown=True):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        timestamps = datetime.datetime.now().strftime(f"%d/%m/%Y %H:%M:%S")
        
        if shown:
            print(f" {Fore.WHITE}[ {timestamps} ] [ INFO ] : {message}{Fore.RESET}", end=end, flush=flush)
        elif DEBUG_MODE == 1:
            print(f" {Fore.WHITE}[ {timestamps} ] [ INFO ] : {message}{Fore.RESET}", end=end, flush=flush)
            
        
        
        logger.info(f" [ {timestamps} ] [ INFO ] : {message}.")
        
    def success_event (message, end="\n", flush=False, shown=True):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        timestamps = datetime.datetime.now().strftime(f"%d/%m/%Y %H:%M:%S")
        
        if shown:
            print(f" {Fore.GREEN}[ {timestamps} ] [ SUCC ] : {message}{Fore.RESET}", end=end, flush=flush)
        elif DEBUG_MODE == 1:
            print(f" {Fore.GREEN}[ {timestamps} ] [ SUCC ] : {message}{Fore.RESET}", end=end, flush=flush)
            
        
        
        logger.info(f"[ {timestamps} ] [ SUCC ] : {message}.")
        
    def warning_event (message, end="\n", flush=False, shown=True):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        timestamps = datetime.datetime.now().strftime(f"%d/%m/%Y %H:%M:%S")
        
        if shown:
            print(f" {Fore.YELLOW}[ {timestamps} ] [ WARN ] : {message}{Fore.RESET}", end=end, flush=flush)
        elif DEBUG_MODE == 1:
            print(f" {Fore.YELLOW}[ {timestamps} ] [ WARN ] : {message}{Fore.RESET}", end=end, flush=flush)
            
        
        
        logger.warning(f"[ {timestamps} ] [ WARN ] : {message}.")
        
    def error_event (message, end="\n", flush=False, shown=True):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        timestamps = datetime.datetime.now().strftime(f"%d/%m/%Y %H:%M:%S")
        
        if shown:
            print(f" {Fore.RED}[ {timestamps} ] [ ERROR ] : {message}{Fore.RESET}", end=end, flush=flush)
        elif DEBUG_MODE == 1:
            print(f" {Fore.RED}[ {timestamps} ] [ ERROR ] : {message}{Fore.RESET}", end=end, flush=flush)
            
        
        
        logger.debug(f"[ {timestamps} ] [ ERROR ] : {message}.")