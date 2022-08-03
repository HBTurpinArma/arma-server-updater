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

##LOGGING STUFF
def my_handler(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        logging.exception(line)
    logging.exception(value)
    if not value =="Script appears to be running already. If this is incorrect please remove .running file.":
        os.remove(f"{PATH_BASE}.running")
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
    for root, dirs, files in os.walk(os.path.join(os.getcwd(), "logs")):
        for name in files:
            logger.info(name)
            if name.endswith(".log"):
                _dts = datetime.strptime(os.path.splitext(name)[0][4:], "%Y%m%d-%H%M%S")
                if (datetime.now() - _dts).total_seconds() > 60 * 60 * 24:
                    logger.info("removing log file: {}".format(name))
                    os.remove(os.path.join(root, name))
    pass


##MOD UPDATING
def call_steamcmd(params):
    os.system("{} {}".format("steamcmd", params))
    # logger.info("{} {}".format("steamcmd", params))

def get_workshop_version(mod_id):
    PATTERN = re.compile(r"workshopAnnouncement.*?<p id=\"(\d+)\">", re.DOTALL)
    WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"
    response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read()
    response = response.decode("utf-8")
    match = PATTERN.search(response)
    if match:
        return datetime.fromtimestamp(int(match.group(1)))

def get_workshop_changelog(mod_id):
    PATTERN = re.compile(r"workshopAnnouncement.*?<p .*?\>(.*?)</p>", re.DOTALL)
    WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"
    response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read()
    response = response.decode("utf-8")
    match = PATTERN.search(response)
    if match:
        return match.group(1).replace("<br>", "\n");

def get_current_version(mod_id, path):
    if os.path.isdir("{}/{}".format(path, mod_id)):
        return datetime.fromtimestamp(os.path.getmtime("{}/{}/meta.cpp".format(path, mod_id)))
    return datetime(1, 1, 1, 0, 0)

def is_updated(mod_id, path):
    workshop_version = get_workshop_version(mod_id)
    logger.info(" Checking https://steamcommunity.com/sharedfiles/filedetails/changelog/{}".format(mod_id))
    logger.info("   Latest Version Found: {}".format(workshop_version))
    current_version = get_current_version(mod_id, path)
    logger.info(" Checking {}{}".format(path, mod_id))
    logger.info("   Current Version Found: {}".format(current_version))

    if not workshop_version or workshop_version == None: #Workshop version can't be found - likely is removed/hidden. No need to keep updating so return true.
        return True

    if current_version:
        return (current_version > workshop_version)  # do we have the most recent file?
    return False

def update_mods(preset, mods):
    mods_to_download = []
    for mod in mods:
        logger.info("\n")
        # Check if mod needs to be updated
        current_version = str(get_current_version(mod["ID"], PATH_STAGING_MODS))
        if os.path.isdir("{}/{}".format(PATH_STAGING_MODS, mod["ID"])):
            if not is_updated(mod["ID"], PATH_STAGING_MODS):
                logger.info("Update required for \"{}\" ({})".format(mod["name"], mod["ID"]))
                # shutil.rmtree(path)  # Delete current version if it exists.
            else:
                logger.info("No update required for \"{}\" ({})... SKIPPING".format(mod["name"], mod["ID"]))
                continue
        else:
            logger.info("No file found, grabbing mod \"{}\" ({})".format(mod["name"], mod["ID"]))


        mods_to_download.append(mod)

        #Add mods to the update file to be read everytime we need to attempt to restart servers
        if not os.path.isfile(f"{PATH_BASE}.update"):
            Path(f"{PATH_BASE}.update").touch()
        with open(f"{PATH_BASE}.update", "a") as update_file:
            update_file.writelines(mod["ID"]+"\n")

    # Download the mod via steamcmd.
    if mods_to_download:
        log("Attempting to download the following mods with steamcmd:")
        steam_cmd_params = " +force_PATH_STAGING {}".format(PATH_STAGING)
        steam_cmd_params += " +login {}".format(STEAM_LOGIN)
        for mod in mods_to_download:
            logger.info("Downloading \"{}\" ({})".format(mod["name"], mod["ID"]))
            steam_cmd_params += " +workshop_download_item {} {} validate".format(WORKSHOP_ID, mod["ID"])
        steam_cmd_params += " +quit"
        call_steamcmd(steam_cmd_params)

    # Send Discord which mods are being updated.
    modHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    for index, mod in enumerate(mods_to_download):
        modEmbed = DiscordEmbed(title='[UPDATE] @{} ({}) has been updated.'.format(mod["name"], mod["ID"]), description='[View Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id={}) | [View Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/{})'.format(mod["ID"],mod["ID"]), color='2121cc')
        modEmbed.add_embed_field(name='Latest Changelog', value=str(get_workshop_changelog(mod["ID"])), inline=False)
        modEmbed.add_embed_field(name='Previous Version', value=current_version)
        modEmbed.add_embed_field(name='Workshop Version', value=str(get_workshop_version(mod["ID"])))
        modEmbed.set_footer(text='Required by ' + preset)
        modHook.add_embed(modEmbed)
        if (index+1) % 10 == 0: #There is a limitation to webhook to being 10 max embeds, so we have to send multiple messages. I don't want to send a whole webhook per mod due to potential spam issues also.
            response = modHook.execute()
            modHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    response = modHook.execute()


def lowercase_mods(stagingPath):
    for path, subdirs, files in os.walk(stagingPath):
        for name in files:
            file_path = os.path.join(path,name)
            new_name = os.path.join(path,name.lower())
            os.rename(file_path, new_name)

# SYMLINK STUFF
def clean_mods(modset):
    _path = os.path.join(PATH_SERVER, modset)
    if os.path.exists(_path) and os.path.isdir(_path):
        shutil.rmtree(_path)
    elif os.path.exists(_path) and not os.path.isdir(_path):
        raise ValueError("Modpack path is not a directory cannot continue")
    os.mkdir(_path)

def symlink_mod(id: str, modpack: str, _modPath:str= None):
    if not _modPath:
        _modPath = os.path.join(PATH_STAGING_MODS, id)
    _destPath = os.path.join(PATH_SERVER, modpack, "@"+id)
    if os.path.exists(_destPath) and os.path.isdir(_destPath):
        shutil.rmtree(_destPath)
    symlink_from_to(_modPath, _destPath)

def symlink_from_to(_modPath, _destPath):
    os.makedirs(os.path.join(_destPath, "addons"), exist_ok=True)
    os.makedirs(os.path.join(_destPath, "keys"), exist_ok=True)
    for root, dirs, files in os.walk(_modPath):
        for name in files:
            if name.endswith(".dll") or name.endswith(".so"):
                try: 
                    os.symlink(os.path.join(root, name), os.path.join(_destPath, name))
                except FileExistsError:
                    pass
            elif name.endswith(".bikey"):
                try:
                    os.symlink(os.path.join(root, name), os.path.join(_destPath, "keys", name))
                except FileExistsError:
                    pass
            elif name.endswith(".pbo") or name.endswith(".ebo") or name.endswith(".bisign"):
                if "optional" in root:
                    pass
                else:
                    try:
                        os.symlink(os.path.join(root, name), os.path.join(_destPath, "addons", name))
                    except FileExistsError:
                        pass
            else:
                continue
            logger.info("Processed {} {}".format(_modPath, name))

def modify_mod_and_meta(id: str, modpack: str, name: str):
    _modPath = os.path.join(PATH_STAGING_MODS, id)
    _destPath = os.path.join(PATH_SERVER, modpack, "@"+id)
    for root, dirs, files in os.walk(_modPath):
        for name in files:
            if name == "mod.cpp" or name == "meta.cpp":
                with open(os.path.join(root, name), "r", encoding='utf8', errors='ignore') as file:
                    _data = file.readlines()
                for i, l in enumerate(_data):
                    if l.startswith("name"):
                        _data[i] = f'name="{id}";\n'
                with open(os.path.join(_destPath, name), "w", encoding="utf-8") as file:
                    file.writelines(_data)
                logger.info("Processed {} {}".format(_modPath, name))


##ONLINE PLAYERS
def notify_players_online(players):
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[ERROR] The servers are being updated.', description='The following users are online.', color='dd2121')
    for k, v in players.items():
        p = ""
        for player in v:
            name = re.findall("(?:name=[\'\"])([\w\[\]\s]+)(?:')", str(player))[0]
            p += name + "\n"
        playerEmbed.add_embed_field(name=k, value=p)
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

def notify_stopping_server(pending):
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[INFO] The servers are being stopped.', description=f'There are {len(pending)} pending servers awaiting updates. These are empty and will be stopped.', color='2121dd')
    server_names = ""
    for server in pending:
        server_names += server['title'] + "\n"
    playerEmbed.add_embed_field(name="Pending Servers", value=server_names)
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

def notify_starting_server(pending):
    playerHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    playerEmbed = DiscordEmbed(title='[INFO] The servers are being started.', description=f'These servers have been updated and are now starting...', color='21dd21')
    server_names = ""
    for server in pending:
        server_names += server['title'] + "\n"
    playerEmbed.add_embed_field(name="Starting Servers", value=server_names)
    playerHook.add_embed(playerEmbed)
    response = playerHook.execute()

def get_online_players(servers):
    players = {}
    for server in servers:
        try:
            _players = (a2s.players(("127.0.0.1", int(server["port"]) + 1,)))
            if len(_players) > 0:
                logger.info(f"There are players on server: {server['title']}")
                players[server['title']] = _players
        except Exception:
            pass
    return players


##PENDING SERVERS
def get_pending_mods():
    mod_ids = []
    with open(f"{PATH_BASE}.update") as update:
        mod_ids = update.read().splitlines() 
    return mod_ids

def get_pending_presets():
    mod_ids = []
    with open(f"{PATH_BASE}.update") as update:
        mod_ids = update.read().splitlines() 
    if isinstance(mod_ids, str): 
        mod_ids = [mod_ids]
    presets = []

    if args.force:
        for preset in os.listdir(PATH_PRESETS):
            presets.append(preset)
            if not os.path.isfile(f"{PATH_BASE}.update"):
                Path(f"{PATH_BASE}.update").touch()
    else:
        for preset in os.listdir(PATH_PRESETS):
            if preset.endswith(".html"):
                preset_mods = loadMods(os.path.join(PATH_PRESETS, preset))
                preset_mods_ids = []
                for preset_mod in preset_mods:
                    preset_mods_ids.append(preset_mod['ID'])

                for mod_id in mod_ids:
                    if mod_id in preset_mods_ids:
                        if preset not in presets:
                            presets.append(preset)
    return presets

def get_pending_servers():
    pending_presets = get_pending_presets()
    pending_mod_ids = get_pending_mods()
    print(get_pending_presets())
    pending_servers = []
    serversJSON = json.load(open(PANEL_SERVERS, "r"))
    for server in serversJSON:
        for server_mod in server["mods"]: #mods_ids
            if server_mod.replace("/","\\").split("\\")[-1] in pending_mod_ids:
                if server not in pending_servers:
                    pending_servers.append(server)
        for server_mod in server["mods"]: #presets
            if server_mod.replace("/","\\").split("\\")[0]+".html" in pending_presets:
                if server not in pending_servers:
                    pending_servers.append(server)
    return pending_servers

def get_server_id(title):
    title = title.lstrip(' ').rstrip(' ') #remove leading whitespace and trailing whitespace
    charMap = json.loads('{"$":"dollar","%":"percent","&":"and","<":"less",">":"greater","|":"or","¢":"cent","£":"pound"," ":"-",".":"-","/":""}')
    for a in charMap:
        title = title.replace(a,charMap[a])
    return title

def stop_server(id):
    try:
        response = requests.post("http://localhost:3000/api/servers/"+id+"/stop", data={""}, auth=(PANEL_LOGIN, PANEL_PASSWORD), timeout=6)
        if response.status_code == requests.codes.ok:
            return True
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        return False
   
def start_server(id):
    try:
        response = requests.post("http://localhost:3000/api/servers/"+id+"/start", data={""}, auth=(PANEL_LOGIN, PANEL_PASSWORD), timeout=6)
        if response.status_code == requests.codes.ok:
            return True
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        return False
    
#RUN
if __name__ == "__main__":
    config_logger()
    sys.excepthook = my_handler

    #Only one instance of the updater can run at a time, stop it running again mid-update.
    if not os.path.isfile(f"{PATH_BASE}.running"):
        Path(f"{PATH_BASE}.update").touch()
        clean_logs()
        
        #For every preset html load in the mods that we need monitor updates on.
        for file in os.listdir(PATH_PRESETS):
            if file.endswith(".html"):
                _name = os.path.splitext(file)[0]
                log("Reading Mod Preset ("+file+")")
                mods = loadMods(os.path.join(PATH_PRESETS, file))
                update_mods(file, mods)
                
        lowercase_mods(PATH_STAGING_MODS) ##Needed for linux :S

        #Logging and notify
        if os.path.isfile(f"{PATH_BASE}.update"):
            pending_servers = get_pending_servers()
            pending_presets = get_pending_presets()

            log("Attempting to update servers:")

            players = get_online_players(pending_servers)
            #Players online, only ever notify once that it can't update as this runs every 5 minutes.
            if players:
                Path(f"{PATH_BASE}.notified").touch()
                if not os.path.isfile(f"{PATH_BASE}.notified"):
                    notify_players_online(players)
            else:  #Players no longer online, so we can stop the service and copy over/symlink the updated mod folders.
                #Attempt to stop all servers that involve pending modpacks
                stopped_servers = []
                for pending_server in pending_servers:
                    success = stop_server(get_server_id(pending_server["title"]))
                    if success:
                        logger.info(pending_server["title"] + " (SUCCESS) Server stop command recieved.")
                        stopped_servers.append(pending_server)
                    else:
                        logger.info(pending_server["title"] + " (FAILED) Server could be offline.")
                notify_stopping_server(stopped_servers)
 
                #Symlink files of pending modpacks
                for file in os.listdir(PATH_PRESETS):
                    if file.endswith(".html"):
                        if file in pending_presets: #Check that is a preset that needs to updated symlink, if so go for it.
                            _name = os.path.splitext(file)[0]
                            log("Processing: {}".format(os.path.join(PATH_PRESETS, file)))
                            clean_mods(_name)
                            mods = loadMods(os.path.join(PATH_PRESETS, file))
                            for m in mods:
                                symlink_mod(m["ID"], _name)
                                modify_mod_and_meta(m["ID"], _name, m["name"])

                #Attempt to start all servers that had been stopped previously
                for stopped_server in stopped_servers:
                    success = start_server(get_server_id(stopped_server["title"]))
                    if success:
                        logger.info(pending_server["title"] + " (SUCCESS) Server start command recieved.")
                    else:
                        logger.info(pending_server["title"] + " (FAILED) Potential issue, server could not be started.")
                notify_starting_server(stopped_servers)

                #Success, lets reset the script to be run again.
                try:
                    os.remove(f"{PATH_BASE}.notified")
                except FileNotFoundError:
                    pass
                    
                try:
                    os.remove(f"{PATH_BASE}.update")
                except FileNotFoundError:
                    pass
        else: 
            log("Mods are up to date, and the server does not need to be restarted.")

        try:  
            os.remove(f"{PATH_BASE}.running")
        except FileNotFoundError:
            pass
    else:
        raise (RuntimeError("Script appears to be running already. If this is incorrect please remove .running file."))
