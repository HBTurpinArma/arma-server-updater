import os
import os.path
from bs4 import BeautifulSoup
from urllib import request
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
import pandas
import csv

#######################################################
config = dotenv_values("../../.env")

PATH_BASE = config["PATH_BASE"]
PATH_STAGING = config["PATH_STAGING"]
PATH_STAGING_MODS = config["PATH_STAGING_MODS"]
PATH_PRESETS = config["PATH_PRESETS"]
PATH_SERVER = config["PATH_SERVER"]
STEAM_LOGIN = config["STEAM_LOGIN"]
STEAM_PASSWORD = config["STEAM_PASSWORD"]
PANEL_SERVERS = config["PANEL_SERVERS"]
PANEL_IP = config["PANEL_IP"]
PANEL_LOGIN = config["PANEL_LOGIN"]
PANEL_PASSWORD = config["PANEL_PASSWORD"]
DISCORD_WEBHOOK = config["DISCORD_WEBHOOK"]



def get_workshop_link(mod_id):
    return f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
    #return f"https://steamcommunity.com/sharedfiles/filedetails/changelog/{mod_id}"

def get_workshop_size(mod_id):
    PATTERN = re.compile(r"detailsStatsContainerRight.*?<div .*?\>(.*?)</div>", re.DOTALL)
    CLEANHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    response = request.urlopen(get_workshop_link(mod_id)).read()
    response = response.decode("utf-8")
    match = PATTERN.search(response)

    if match:
        string_size = re.sub(CLEANHTML, '', match.group(1).replace("<br>", "\n").replace("</b>", "\n"))
        clean_number = float(string_size[:-3])
        if "KB" in string_size:
            return round(clean_number / 1000000,5)
        elif "MB" in string_size:
            return round(clean_number / 1000,5)
        elif "GB" in string_size:
            return round(clean_number / 1,5)
        else:
            return 0
    else:
        return ""


def get_workshop_required_item_ids(mod_id):
    response = request.urlopen(get_workshop_link(mod_id)).read()
    soup = BeautifulSoup(response, 'html.parser')

    # Find the container with the required items
    required_items_container = soup.find('div', class_='requiredItemsContainer')

    if required_items_container:
        # Extract all links with IDs in the required items container
        links = required_items_container.find_all('a', href=True)
        ids = []
        for link in links:
            match = re.search(r'id=(\d+)', link['href'])
            if match:
                ids.append(match.group(1))
        print(ids)
        return ids



#######################################################


if __name__ == "__main__":
    presets = []

    core_mods = get_workshop_required_item_ids("3038124203") or []
    map_mods = get_workshop_required_item_ids("3038082542") or []
    am2_mods = get_workshop_required_item_ids("2293037577") or []

    for preset in os.listdir(PATH_PRESETS):
        mods = []
        if preset.endswith(".html"):
            preset_mods = loadMods(os.path.join(PATH_PRESETS, preset))
            for preset_mod in preset_mods:
                print(preset_mod)
                preset_pack = "Unknown"
                if preset_mod["ID"] in core_mods:
                    preset_pack = "Core"
                elif preset_mod["ID"] in map_mods:
                    preset_pack = "Maps"
                elif preset_mod["ID"] in am2_mods:
                    preset_pack = "AM2 Main"

                mod = {"NAME": preset_mod["name"], "ID": preset_mod["ID"], "LINK": get_workshop_link(preset_mod["ID"]), "SIZE": get_workshop_size(preset_mod["ID"]), "PRESET": preset_pack}
                print(mod)

                mods.append(mod)

            keys = mods[0].keys()
            with open(f'{preset[:-5]}.csv', 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(mods)