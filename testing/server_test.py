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


parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--force", action="store_true", help="force an update of every preset and re-symlink.")
args = parser.parse_args()

##CONFIGSTART
config = dotenv_values("../.env")

PANEL_SERVERS = config["PANEL_SERVERS"]
PANEL_IP = config["PANEL_IP"]
PANEL_LOGIN = config["PANEL_LOGIN"]
PANEL_PASSWORD = config["PANEL_PASSWORD"]

def get_server_id(title):
    title = title.lstrip(' ').rstrip(' ')
    charMap = json.loads('{"$":"dollar","%":"percent","&":"and","<":"less",">":"greater","|":"or","¢":"cent","£":"pound"," ":"-",".":"-","/":""}')
    for a in charMap:
        title = title.replace(a,charMap[a])
    return title

def restartheadless(id):
    response = requests.post("http://localhost:4000/api/servers/"+id+"/headlessrefresh", data={""}, auth=(PANEL_LOGIN, PANEL_PASSWORD), timeout=3)
    print(response)




if __name__ == "__main__":
    restartheadless("Testing")
