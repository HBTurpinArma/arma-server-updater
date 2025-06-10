import os
import os.path
import re
import shutil
import sys
import logging
import sys
import traceback
import json
from datetime import datetime
from urllib import request
from discord_webhook import DiscordWebhook, DiscordEmbed
from pathlib import Path
import a2s
from process_html import loadMods
from dotenv import dotenv_values
import requests
from pathlib import Path
import argparse

##ADDITIONAL ARGUMENTS FOR SCRIPT
parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--force", action="store_true", help="force an update of every preset and re-symlink.")
parser.add_argument("-d", "--discord", action="store_true", help="enables use of the discord webhook to notify actions")
args = parser.parse_args()

##CONFIGSTART
config = dotenv_values("../.env")

SERVER_ID = "233780"
WORKSHOP_ID = "107410"

PATH_BASE = config["PATH_BASE"]
PATH_STAGING = config["PATH_STAGING"]
PATH_STAGING_MODS = config["PATH_STAGING_MODS"]
PATH_PRESETS = config["PATH_PRESETS"]
PATH_SERVER = config["PATH_SERVER"]

STEAM_LOGIN = config["STEAM_LOGIN"]
STEAM_PASSWORD = config["STEAM_PASSWORD"] #NOT USED - BUT MAY WANT TO IF CREDENTIAL CACHING BECOMES A PROBLEM

PANEL_SERVERS = config["PANEL_SERVERS"]
PANEL_IP = config["PANEL_IP"]
PANEL_LOGIN = config["PANEL_LOGIN"]
PANEL_PASSWORD = config["PANEL_PASSWORD"]

DISCORD_WEBHOOK = config["DISCORD_WEBHOOK"]

##LOGGING STUFF
def my_handler(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        logging.exception(line)
    logging.exception(value)
    if not value =="Script appears to be running already. If this is incorrect please remove .running file.":
        try:
            os.remove(f"{PATH_BASE}.running")
        except Exception:
            pass
    sys.__excepthook__(type, value, tb)  # calls default excepthook

# Install exception handler
logger = logging.getLogger(__name__)
logger.info(config)

def config_logger():
    os.makedirs(f"{PATH_BASE}logs", exist_ok=True)
    _now = datetime.now().strftime("%Y%m%d-%H%M%S")
    logging.basicConfig(filename="{}logs/log_{}.log'".format(PATH_BASE, _now), level=logging.DEBUG)
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
    for root, dirs, files in os.walk(os.path.join(PATH_BASE, "logs")):
        for name in files:
            logger.info(name)
            if name.endswith(".log"):
                _dts = datetime.strptime(os.path.splitext(name)[0][4:], "%Y%m%d-%H%M%S")
                if (datetime.now() - _dts).total_seconds() > 60 * 60 * 24:
                    logger.info("removing log file: {}".format(name))
                    os.remove(os.path.join(root, name))
    pass





##DISCORD WEBHOOK PLAYERS
def notify_players_online(players):
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[ERROR] The servers are pending updates but are not empty.', description='The following users are online.', color='dd2121')
    for k, v in players.items():
        p = ""
        for player in v:
            name = re.findall("(?<=name=').*?(?=',)", str(player))[0]
            p += name + "\n"
        playerEmbed.add_embed_field(name=k, value=p)
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

def get_online_players(servers):
    players = {}
    for server in servers:
        try:
            _players = (a2s.players(("148.251.67.92", int(server["port"]) + 1,)))
            logger.info(f"There are {len(_players)} players on server: {server['title']}")
            logger.info(_players)
            if len(_players) > 0:
                players[server['title']] = _players
        except Exception:
            logger.info(f"{server['title']} is offline or cannot be found.")
    return players


def get_servers():
    servers = []
    serversJSON = json.load(open(PANEL_SERVERS, "r"))
    for server in serversJSON:
        if server not in servers:
            servers.append(server)
    return servers

if __name__ == "__main__":
    config_logger()
    sys.excepthook = my_handler

    servers = get_servers()
    #Players online, only ever notify once that it can't update as this runs every X minutes.
    log("Checking if servers have players online:")
    players = get_online_players(servers)
    print(players)
    notify_players_online(players)




