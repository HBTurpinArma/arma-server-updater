import argparse
import asyncio
import json
import logging
import os
import os.path
import re
import subprocess
import sys
import traceback
from datetime import datetime
import a2s
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import dotenv_values

#######################################################

parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-d", "--discord", action="store_true", help="disables use of the discord webhook to notify actions.")
args = parser.parse_args()

#######################################################

config = dotenv_values(".env")

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

#######################################################

def my_handler(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        logging.exception(line)
    logging.exception(value)
    if not value =="Script appears to be running already. If this is incorrect please remove .running file.":
        os.remove(".running")
    sys.__excepthook__(type, value, tb)  # calls default excepthook

# Install exception handler
logger = logging.getLogger(__name__)
logger.info(config)

def config_logger():
    os.makedirs("logs", exist_ok=True)
    _now = datetime.now().strftime("%Y%m%d-%H%M%S")
    logging.basicConfig(filename='logs/update_game_{}.log'.format(_now), level=logging.DEBUG)
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
                _dts = datetime.strptime(os.path.splitext(name)[0][12:], "%Y%m%d-%H%M%S")
                if (datetime.now() - _dts).total_seconds() > 60 * 60 * 24 * 31:
                    logger.info("removing log file: {}".format(name))
                    os.remove(os.path.join(root, name))

#######################################################

async def stop_servers(servers):
    # Run all stop_server coroutines concurrently
    await asyncio.gather(*[stop_server(server) for server in servers])

async def stop_server(server):
    try:
        response = await asyncio.to_thread(
            requests.post,
            f"http://localhost:3000/api/servers/{server['uid']}/stop",
            data={""},
            auth=(PANEL_LOGIN, PANEL_PASSWORD),
            timeout=6
        )
        if response.status_code == requests.codes.ok:
            logger.info(f"{server['title']} ({server['uid']}) (SUCCESS) Server stop command received.")
            return
    except requests.exceptions.RequestException:
        pass
    logger.info(f"{server['title']} ({server['uid']}) (FAILED) Server could be offline.")

def get_online_players(servers):
    players = {}
    for server in servers:
        try:
            _players = (a2s.players(("127.0.0.1", int(server["port"]) + 1)))
            logger.info(f"There are {len(_players)} players on server: {server['title']} ({server['uid']})")
            logger.info(_players)
            if len(_players) > 0:
                players[server['title']] = _players
        except Exception:
            logger.info(f"{server['title']} is offline or cannot be found.")
    return players

#######################################################

def notify_stopping_servers():
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[INFO] Restarting all servers', description=f'All servers are being stopped to perform a game and dlc update, all currently online servers will reboot once the update has finished.', color='2121dd')
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

def notify_players_online(players):
    if args.discord: return
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

#######################################################

def call_steamcmd(params):
    command = f"steamcmd {params}"
    logger.info(f"Running 'steamcmd' Command: {command}")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if stdout:
            logger.info(f"steamcmd output:\n{stdout}")
        if stderr:
            logger.error(f"steamcmd errors:\n{stderr}")

        if process.returncode != 0:
            logger.error(f"steamcmd exited with code {process.returncode}")
    except Exception as e:
        logger.exception(f"Failed to run steamcmd: {e}")

def update_game():
    steam_cmd_params = " +force_install_dir {}".format(PATH_SERVER)
    steam_cmd_params += " +login {}".format(STEAM_LOGIN)
    steam_cmd_params += ' +app_update 233780 -beta creatordlc validate +quit {}'.format(SERVER_ID)
    call_steamcmd(steam_cmd_params)

#######################################################

if __name__ == "__main__":
    config_logger()
    sys.excepthook = my_handler
    if args.discord:
        logger.info("Discord notifications are disabled, no notifications will be sent.")

    #Cleanup logs
    logger.info("Cleaning up old log files...")
    clean_logs()

    #Get all the servers from the panel
    servers = json.load(open(PANEL_SERVERS, "r"))

    #Check for online players
    log("Checking for online players:")
    players = get_online_players(servers)

    if players:
        notify_players_online(players)
    else:
        #Stop all servers
        log("Attempting to stop servers:")
        notify_stopping_servers()
        asyncio.run(stop_servers(servers))

        #Update the game
        log("Attempting to update the game:")
        update_game()

