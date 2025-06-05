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
import asyncio
import aiohttp

#######################################################

parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--force", action="store_true", help="force an update of every preset and re-symlink.")
parser.add_argument("-d", "--discord", action="store_true", help="disables use of the discord webhook to notify actions.")
parser.add_argument("-s", "--symlink", action="store_true", help="forces the symlink process regardless if any mods updated.")
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
STEAM_PASSWORD = config["STEAM_PASSWORD"]  # NOT USED - BUT MAY WANT TO IF CREDENTIAL CACHING BECOMES A PROBLEM
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
    if not value == "Script appears to be running already. If this is incorrect please remove .running file.":
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


#######################################################

async def get_workshop_version(mod_id):
    PATTERN = re.compile(r"workshopAnnouncement.*?<p id=\"(\d+)\">", re.DOTALL)
    WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{WORKSHOP_CHANGELOG_URL}/{mod_id}") as response:
            response_text = await response.text()
            match = PATTERN.search(response_text)
            if match:
                return datetime.fromtimestamp(int(match.group(1)))
    return datetime(1, 1, 1, 0, 0)


def get_workshop_changelog(mod_id):
    PATTERN = re.compile(r"workshopAnnouncement.*?<p .*?\>(.*?)</p>", re.DOTALL)
    CLEANHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"
    response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read()
    response = response.decode("utf-8")
    match = PATTERN.search(response)
    if match:
        return re.sub(CLEANHTML, '', match.group(1).replace("<br>", "\n").replace("</b>", "\n"))
    return ""


async def get_current_version(mod_id, path):
    mod_path = "{}/{}".format(path, mod_id)
    if os.path.isdir(mod_path):
        meta_file = "{}/meta.cpp".format(mod_path)
        mod_file = "{}/mod.cpp".format(mod_path)
        if os.path.isfile(meta_file):
            return datetime.fromtimestamp(os.path.getmtime(meta_file))
        elif os.path.isfile(mod_file):
            return datetime.fromtimestamp(os.path.getmtime(mod_file))
    return datetime(1, 1, 1, 0, 0)


async def is_mod_updated(mod_id, path):
    workshop_version = await get_workshop_version(mod_id)
    logger.info(" Checking https://steamcommunity.com/sharedfiles/filedetails/changelog/{}".format(mod_id))
    logger.info("   Latest Version Found: {}".format(workshop_version))
    current_version = await get_current_version(mod_id, path)
    logger.info(" Checking {}{}".format(path, mod_id))
    logger.info("   Current Version Found: {}".format(current_version))
    if current_version == datetime(1, 1, 1, 0, 0):
        logger.info("   No current version found, assuming update is required.")
        return False
    if workshop_version == datetime(1, 1, 1, 0, 0):  # Workshop version can't be found - likely is removed/hidden. No need to keep updating so return true.
        logger.info("   Couldn't obtain workshop version, suggesting no update is required.")
        return True
    if current_version:
        return (current_version > workshop_version)  # do we have the most recent file?
    return False


pending_mods = []


async def get_pending_mods():
    tasks = []  # List to hold tasks
    for file in os.listdir(PATH_PRESETS):
        if file.endswith(".html"):
            # log("Reading Mod Preset (" + file + ")")
            mods = loadMods(os.path.join(PATH_PRESETS, file))
            for mod in mods:
                mod_id_path = os.path.join(PATH_STAGING_MODS, mod["ID"])
                if os.path.isdir(mod_id_path):
                    # Create a task for checking if the mod needs to be updated
                    tasks.append(check_mod_update(mod, mod_id_path))
                else:
                    logger.info("No file found, grabbing mod \"{}\" ({})".format(mod["name"], mod["ID"]))
                    pending_mods.append(mod)

    # Await all the tasks
    await asyncio.gather(*tasks)


async def check_mod_update(mod, mod_id_path):
    if not await is_mod_updated(mod["ID"], PATH_STAGING_MODS) or args.force:
        logger.info("Update required for \"{}\" ({}) \n".format(mod["name"], mod["ID"]))
        if mod not in pending_mods:
            pending_mods.append(mod)
    else:
        logger.info("No update required for \"{}\" ({})... SKIPPING \n".format(mod["name"], mod["ID"]))


#######################################################

def call_steamcmd(params):
    os.system("{} {}".format("steamcmd", params))  # logger.info("{} {}".format("steamcmd", params))


def update_mods(mods):
    if not mods: return
    steam_cmd_params = " +force_install_dir {}".format(PATH_STAGING)
    steam_cmd_params += " +login {}".format(STEAM_LOGIN)
    for mod in mods:
        logger.info("Downloading \"{}\" ({})".format(mod["name"], mod["ID"]))
        steam_cmd_params += " +workshop_download_item {} {} validate".format(WORKSHOP_ID, mod["ID"])
    steam_cmd_params += " +quit"
    logger.info(f"Running SteamCMD with the following parameters: {steam_cmd_params}")
    call_steamcmd(steam_cmd_params)
    asyncio.run(notify_updated_mods(mods))


#######################################################

def lowercase_mods(stagingPath):
    for path, subdirs, files in os.walk(stagingPath):
        for name in files:
            file_path = os.path.join(path, name)
            new_name = os.path.join(path, name.lower())
            os.rename(file_path, new_name)


def clean_mods(modset):
    _path = os.path.join(PATH_SERVER, modset)
    if os.path.exists(_path) and os.path.isdir(_path):
        shutil.rmtree(_path)
    elif os.path.exists(_path) and not os.path.isdir(_path):
        raise ValueError("Modpack path is not a directory cannot continue")
    os.mkdir(_path)


def symlink_mod(id: str, modpack: str, _modPath: str = None):
    if not _modPath:
        _modPath = os.path.join(PATH_STAGING_MODS, id)
    _destPath = os.path.join(PATH_SERVER, modpack, "@" + id)
    if os.path.exists(_destPath) and os.path.isdir(_destPath):
        shutil.rmtree(_destPath)
    symlink_from_to(_modPath, _destPath)


def symlink_from_to(_modPath, _destPath):
    os.makedirs(os.path.join(_destPath, "addons"), exist_ok=True)
    os.makedirs(os.path.join(_destPath, "keys"), exist_ok=True)
    ignore_list = ["optional", "optionals", "Optional", "Optionals", "compats", "Compats", "compat", "Compat"]
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
                if any(ignore_word in root for ignore_word in ignore_list):
                    pass
                else:
                    try:
                        os.symlink(os.path.join(root, name), os.path.join(_destPath, "addons", name))
                    except FileExistsError:
                        pass
            else:
                continue
            logger.info("Processed {} {}".format(_modPath, name))


def modify_mod_and_meta(id: str, modpack: str, modName: str):
    _modPath = os.path.join(PATH_STAGING_MODS, id)
    _destPath = os.path.join(PATH_SERVER, modpack, "@" + id)
    for root, dirs, files in os.walk(_modPath):
        for name in files:
            if name == "mod.cpp" or name == "meta.cpp":
                with open(os.path.join(root, name), "r", encoding='utf8', errors='ignore') as file:
                    _data = file.readlines()
                for i, l in enumerate(_data):
                    if l.startswith("name=") or l.startswith("name "):
                        _data[i] = f'name="{modName}";\n'
                with open(os.path.join(_destPath, name), "w", encoding="utf-8") as file:
                    file.writelines(_data)
                logger.info("Processed {} {}".format(_modPath, name))


#######################################################

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


def notify_stopping_server(pending):
    if args.discord or not pending: return
    serverHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    serverEmbed = DiscordEmbed(title='[INFO] The servers are being stopped.', description=f'There are {len(pending)} pending servers awaiting updates. These are empty and will be stopped.', color='2121dd')
    server_names = ""
    for server in pending:
        server_names += server['title'] + "\n"
    serverEmbed.add_embed_field(name="Pending Servers", value=server_names)
    serverHook.add_embed(serverEmbed)
    response = serverHook.execute()


def notify_symlink():
    if args.discord: return
    symlinkHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    symlinkEmbed = DiscordEmbed(title='[INFO] Updated mod files have been symlinked over to the servers.', description=f'', color='21dd21')
    symlinkHook.add_embed(symlinkEmbed)
    response = symlinkHook.execute()


def notify_starting_server(pending):
    if args.discord or not pending: return
    serverHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    serverEmbed = DiscordEmbed(title='[INFO] The servers are being started.', description=f'These servers have been updated and are now starting...', color='2121dd')
    server_names = ""
    for server in pending:
        server_names += server['title'] + "\n"
    serverEmbed.add_embed_field(name="Starting Servers", value=server_names)
    serverHook.add_embed(serverEmbed)
    response = serverHook.execute()


async def notify_updated_mods(mods):
    if args.discord: return
    modHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    webhookCount = 0
    webhookSize = 0
    for mod in mods:
        modEmbed = DiscordEmbed(title='[UPDATE] @{} ({}) has been updated.'.format(mod["name"], mod["ID"]),
                                description='[View Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id={}) | [View Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/{})'.format(mod["ID"], mod["ID"]),
                                color='2121cc')
        workshopChangelog = get_workshop_changelog(mod["ID"])[:1000] + "..."
        modEmbed.add_embed_field(name='Latest Changelog', value=str(workshopChangelog) or "", inline=False)
        modEmbed.add_embed_field(name='Previous Version', value=str(await get_current_version(mod["ID"], PATH_STAGING_MODS) or ""))
        modEmbed.add_embed_field(name='Workshop Version', value=str(await get_workshop_version(mod["ID"])) or "")
        # modEmbed.set_footer(text='Required by ' + preset)
        modHook.add_embed(modEmbed)
        # Obtain current size of embed for limit checking
        webhookSize += len(workshopChangelog)
        webhookCount += 1
        logger.info("Adding info into webhook for {} (@{}) | Count: {} | Size: {} | Total: {}".format(mod["name"], mod["ID"], webhookCount, len(workshopChangelog), webhookSize))
        if (webhookCount) % 10 == 0 or webhookSize > 4000:  # There is a limitation to webhook to being 10 max embeds, and a size limit of 6000, we save 2000 space for rest of text.
            response = modHook.execute()
            modHook = DiscordWebhook(url=DISCORD_WEBHOOK)
            webhookCount = 0
            webhookSize = 0
    response = modHook.execute()


#######################################################

def get_pending_presets(mods):
    presets = []
    for preset in os.listdir(PATH_PRESETS):

        if preset.endswith(".html"):
            if args.symlink or args.force or os.path.isfile(f"{PATH_BASE}.symlink_pending"):
                presets.append(preset)
                continue
            preset_mods = loadMods(os.path.join(PATH_PRESETS, preset))
            preset_mods_ids = []
            for preset_mod in preset_mods:
                preset_mods_ids.append(preset_mod["ID"])

            for mod in mods:
                if mod["ID"] in preset_mods_ids:
                    if preset not in presets:
                        presets.append(preset)
    return presets


def get_pending_servers(mods, pending_presets):
    pending_mod_ids = []
    pending_servers = []
    for mod in mods:
        pending_mod_ids.append(mod["ID"])
    serversJSON = json.load(open(PANEL_SERVERS, "r"))
    for server in serversJSON:
        if server['game_selected'] == "arma3":
            for server_mod in server["mods"] + server['mods_optional'] + server['mods_server_only']:  # mods_ids
                if server_mod.replace("/", "\\").split("\\")[-1] in pending_mod_ids:  # Technically could just use the presets check...
                    if server not in pending_servers:
                        pending_servers.append(server)
                if server_mod.replace("/", "\\").split("\\")[0] + ".html" in pending_presets:
                    if server not in pending_servers:
                        pending_servers.append(server)
    return pending_servers


def get_server_id(title):
    title = title.lstrip(' ').rstrip(' ')  # remove leading whitespace and trailing whitespace
    charMap = json.loads('{"$":"dollar","%":"percent","&":"and","<":"less",">":"greater","|":"or","¢":"cent","£":"pound"," ":"-",".":"-","/":"","#":""}')
    for a in charMap:
        title = title.replace(a, charMap[a])
    return title


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
            pass  # logger.info(f"{server['title']} is offline or cannot be found.")
    return players


#######################################################

stopped_servers = []

async def stop_pending_servers(servers):
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
            stopped_servers.append(server)
            logger.info(f"{server['title']} ({server['uid']}) (SUCCESS) Server stop command received.")
            return
    except requests.exceptions.RequestException:
        pass
    logger.info(f"{server['title']} ({server['uid']}) (FAILED) Server could be offline.")

async def start_stopped_servers(servers):
    # Run all start_server coroutines concurrently
    await asyncio.gather(*[start_server(server) for server in servers])

async def start_server(server):
    try:
        response = await asyncio.to_thread(
            requests.post,
            f"http://localhost:3000/api/servers/{server['uid']}/start",
            data={""},
            auth=(PANEL_LOGIN, PANEL_PASSWORD),
            timeout=6
        )
        if response.status_code == requests.codes.ok:
            logger.info(f"{server['title']} ({server['uid']}) (SUCCESS) Server start command received.")
            return
    except requests.exceptions.RequestException:
        pass
    logger.info(f"{server['title']} ({server['uid']}) (FAILED) Server could be offline.")

#######################################################

if __name__ == "__main__":
    config_logger()
    sys.excepthook = my_handler
    if args.force:
        logger.info("Forcing is enabled, all mods will be updated/validated and symlinked.")
    if args.symlink:
        logger.info("Symlink Forcing is enabled, all mods will be symlinked regardless of mod updates.")
    if args.discord:
        logger.info("Discord notifications are disabled, no notifications will be sent.")

    # Only one instance of the updater can run at a time, stop it running again mid-update.
    if not os.path.isfile(f"{PATH_BASE}.running"):
        Path(f"{PATH_BASE}.running").touch()
        clean_logs()

        asyncio.run(get_pending_mods())
        print(pending_mods)
        if pending_mods or args.symlink or os.path.isfile(f"{PATH_BASE}.symlink_pending"):
            # Check which presets are affected from updated mods as the whole preset gets symlinked.
            pending_presets = get_pending_presets(pending_mods)
            log("The following mod presets need to be symlinked:")
            for preset in pending_presets:
                logger.info(preset)

            # Check which servers are affected as a result of using either a preset / mod for the pending lists.
            pending_servers = get_pending_servers(pending_mods, pending_presets)
            log("The following servers need to be restarted:")
            for server in pending_servers:
                logger.info(server["title"])
            if not pending_servers:
                logger.info("No pending servers to stop, skipping...")

            # Players online, only ever notify once that it can't update as this runs every X minutes.
            players = get_online_players(pending_servers)
            if players:
                if not os.path.isfile(f"{PATH_BASE}.notified"):
                    notify_players_online(players)
                    Path(f"{PATH_BASE}.notified").touch()
            else:
                # Players no longer online, so we can stop the servers and copy over/symlink the updated mod folders.
                log("Attempting to stop servers:")
                if pending_servers:
                    asyncio.run(stop_pending_servers(pending_servers))
                    notify_stopping_server(stopped_servers)
                else:
                    logger.info("No pending servers to stop, skipping...")

                # Download the mods now that servers are offline and then symlink them.
                log(f"Attempting to update mods:")
                update_mods(pending_mods)

                # Mods updated, add in a symlink pending tag for future runs if the below fails
                Path(f"{PATH_BASE}.symlink_pending").touch()

                # Symlink files of pending modpacks
                for file in os.listdir(PATH_PRESETS):
                    if file.endswith(".html"):
                        if file in pending_presets:  # Check that is a preset that needs to updated symlink, if so go for it.
                            _name = os.path.splitext(file)[0]
                            log("Attempting to symlink preset: {}".format(os.path.join(PATH_PRESETS, file)))
                            clean_mods(_name)
                            mods = loadMods(os.path.join(PATH_PRESETS, file))
                            for m in mods:
                                symlink_mod(m["ID"], _name)
                                modify_mod_and_meta(m["ID"], _name, m["name"])
                try:
                    os.remove(f"{PATH_BASE}.symlink_pending")
                except FileNotFoundError:
                    pass

                # Notify that the symlinks have started to push the updates to the servers.
                notify_symlink()

                # Attempt to start all servers that had been stopped previously
                log(f"Attempting to start servers:")
                if stopped_servers:
                    asyncio.run(start_stopped_servers(stopped_servers))
                    notify_starting_server(stopped_servers)
                else:
                    logger.info("No servers to start, skipping...")

                # Success, lets reset the script to be run again.
                try:
                    os.remove(f"{PATH_BASE}.notified")
                except FileNotFoundError:
                    pass
        else:
            # No updates were required.
            log("Mods are up to date, and the server does not need to be restarted.")

        # Allow script to be rerun.
        try:
            os.remove(f"{PATH_BASE}.running")
        except FileNotFoundError:
            pass
    else:
        # Only allow one singular instance of the script to be running at one time, if not error out.
        raise (RuntimeError("Script appears to be running already. If this is incorrect please remove .running file."))
