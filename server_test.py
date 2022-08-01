import os
import os.path
import re
import shutil
import sys
import logging
import sys
import traceback
from webbrowser import get
import json
from datetime import datetime
from urllib import request
from pprint import pprint
from discord_webhook import DiscordWebhook, DiscordEmbed
from pathlib import Path
import a2s
import process_html
from process_html import loadMods
from dotenv import dotenv_values
import requests
import hashlib
from _hashlib import HASH as Hash
from pathlib import Path
from typing import Union

config = dotenv_values(".env")

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

DISCORD_WEBHOOK = config[
    "DISCORD_WEBHOOK"]  # 'https://discord.com/api/webhooks/909859742774611999/HcU7v8b0c5Ce9QKK9EGkAeDaVw7tp37ge5orFjWpxaNSdCid7ulABPxKDomWc13B11HO'
SERVERS_JSON_FILE = config["SERVERS_JSON_FILE"]  # "C:/arma-server-web-admin/servers.json"

def get_server_id(title):
    title = title.lstrip(' ').rstrip(' ')
    charMap = json.loads('{"$":"dollar","%":"percent","&":"and","<":"less",">":"greater","|":"or","¢":"cent","£":"pound"," ":"-",".":"-","/":""}')
    for a in charMap:
        title = title.replace(a,charMap[a])
    return title

def stop_server(id):
    try:
        response = requests.post("http://78.46.78.85:3000/api/servers/"+id+"/stop", data={""}, auth=(PANEL_LOGIN, PANEL_PASS), timeout=3)
        if response.status_code == requests.codes.ok:
            return True
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        return False
   
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
#RUN
if __name__ == "__main__":
    #print(stop_server(get_server_id("4th Legion | STARNR ")))
    # print(get_workshop_changelog(2383887543))
    # mod = {'name': "327th Brokkrs Workshop", "ID":"2383887543"}
    # modHook = DiscordWebhook(url=DISCORD_WEBHOOK)
    # modEmbed = DiscordEmbed(title='[UPDATE] @{} ({}) has been updated.'.format(mod["name"], mod["ID"]), description='[View Workshop Link](https://steamcommunity.com/sharedfiles/filedetails/?id={}) | [View Workshop Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/{})'.format(mod["ID"],mod["ID"]), color='2121cc', inline=False)
    # modEmbed.add_embed_field(name='Latest Changelog', value=str(get_workshop_changelog(mod["ID"])), inline=False)
    # modEmbed.add_embed_field(name='Previous Version', value="00:00:00")
    # modEmbed.add_embed_field(name='Workshop Version', value=str(get_workshop_version(mod["ID"])))
    # modEmbed.set_footer(text='Required by ' + "4th.html")
    # modHook.add_embed(modEmbed)
    # response = modHook.execute()
