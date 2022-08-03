import os
import os.path
import shutil
import sys
import logging
import sys
import traceback
import json
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import dotenv_values
import requests
from distutils.dir_util import copy_tree

config = dotenv_values(".env")

def my_handler(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        logging.exception(line)
    logging.exception(value)
    if not value =="Script appears to be running already. If this is incorrect please remove .running file.":
        os.remove(".running")
    sys.__excepthook__(type, value, tb)  # calls default excepthook

# Install exception handler

logger = logging.getLogger(__name__)

##CONFIGSTART
SERVER_ID = "233780"
WORKSHOP_ID = "107410"
 
INSTALL_DIR = config["INSTALL_DIR"]
CHECK_DIR = config["CHECK_DIR"]
CONFIG_DIR = config["CONFIG_DIR"]
ARMA_DIR = config["ARMA_DIR"]
STEAMCMD_PATH = config["STEAMCMD_PATH"] 

STEAM_LOGIN = config["STEAM_LOGIN"]
PANEL_LOGIN = config["PANEL_LOGIN"]
PANEL_PASS = config["PANEL_PASS"]

DISCORD_WEBHOOK = config["DISCORD_WEBHOOK"]
SERVERS_JSON_FILE = config["SERVERS_JSON_FILE"]

logger.info(config)

##LOGGING STUFF
def config_logger():
    os.makedirs("logs", exist_ok=True)
    _now = datetime.now().strftime("%Y%m%d-%H%M%S")
    logging.basicConfig(filename='logs/log_{}.log'.format(_now), level=logging.DEBUG)
    # Configure logger to write to a file...
    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

def log(msg):
    logger.info("")
    logger.info("{{0:=<{}}}".format(len(msg)).format(""))
    logger.info(msg)
    logger.info("{{0:=<{}}}".format(len(msg)).format(""))

def clean_logs():
    for root, dirs, files in os.walk(os.path.join(os.getcwd(), "logs")):
        for name in files:
            logger.info(name)
            if name.endswith(".log"):
                _dts = datetime.strptime(os.path.splitext(name)[0][4:], "%Y%m%d-%H%M%S")
                if (datetime.now() - _dts).total_seconds() > 60 * 60 * 24:
                    logger.info("removing log file: {}".format(name))
                    os.remove(os.path.join(root, name))

##GAME UPDATE STUFF
def call_steamcmd(params):
    logger.info("{} {}".format("steamcmd", params))
    os.system("{} {}".format("steamcmd", params))

def extract_dlc(path):
    copy_tree(path, ARMA_DIR)

def update_game():
    steam_cmd_params = " +force_install_dir {}".format(ARMA_DIR)
    steam_cmd_params += " +login {}".format(STEAM_LOGIN)
    steam_cmd_params += ' +app_update 233780 -beta creatordlc " validate +quit {}'.format(SERVER_ID)

    call_steamcmd(steam_cmd_params)
        
def notify_stopping_server():
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[INFO] Restarting all servers', description=f'All servers are being stopped to perform a game and dlc update, all currently online servers will reboot once the update has finished.', color='2121dd')
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

##SERVER STUFF
def get_server_id(title):
    title = title.lstrip(' ').rstrip(' ') #remove leading whitespace and trailing whitespace
    charMap = json.loads('{"$":"dollar","%":"percent","&":"and","<":"less",">":"greater","|":"or","¢":"cent","£":"pound"," ":"-",".":"-","/":""}')
    for a in charMap:
        title = title.replace(a,charMap[a])
    return title

def stop_server(id):
    try:
        response = requests.post("http://localhost:3000/api/servers/"+id+"/stop", data={""}, auth=(PANEL_LOGIN, PANEL_PASS), timeout=6)
        if response.status_code == requests.codes.ok:
            return True
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        return False
   
def start_server(id):
    try:
        response = requests.post("http://localhost:3000/api/servers/"+id+"/start", data={""}, auth=(PANEL_LOGIN, PANEL_PASS), timeout=6)
        if response.status_code == requests.codes.ok:
            return True
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        return False
    
if __name__ == "__main__":
    update_game()

