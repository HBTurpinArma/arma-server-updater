##Read in the killcounts from the txt file using regex and print them out in a formatted way.
import re
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont
import json

kill_data = {}

def get_log_data():
    with open('S:\\Github\\HBTurpinArma\\arma-server-updater\\testing\\logs.rpt', 'r') as f:
        data = f.read()

    full_player_list = []
    #Go through the log file line by line:
    for line in data.splitlines():
        players = None
        if "ace_medical_treatment_fnc_treatment" in line:
            pass
            # Find each player and their kill counts using regex
            # player_pattern = r"Player:\s+(.+?)\s+used.*?\son\s(.+?)\s*\|.*?\((.+?)\)"
            # players = re.findall(player_pattern, line, re.DOTALL)
        #23:29:39 2025-12-05 22:29:39:242 | Antistasi | Info | File: A3A_fnc_requestSupport | Requested support against R The Baubles - 42:2 (DynCoder [RPG]) REMOTE from [13294.7,6164.75,0.00194359] by side WEST
        elif "A3A_fnc_requestSupport" in line:
            pass
            # pattern = r"\(([^[]+?)\s*\["
            # players = re.findall(pattern, line, re.DOTALL)
        #23:34:33 2025-12-05 22:34:33:989 | Antistasi | Info | File: HR_GRG_fnc_addVehicle | By: Kaelies [AM 2] [76561198025224096] | Type: Offroad (UP) | Vehicle ID: 39 | Lock: false | Source: -1
        elif "HR_GRG_fnc_addVehicle" in line:
            pass
            # pattern = r"By:\s+([^\[]+?)\s*(?=\[|$)"
            # players = re.findall(pattern, line, re.DOTALL)
        #23:24:35 (3:25:26) cba_versioning - zhc - Version Mismatch! (Machine: R PL / ZEUS on 71 40:4 (Asru [AM 2]) (Asru [AM 2]) version:
        elif "zhc - Version Mismatch!" in line:
            pattern = r"Machine:[^()]*\(\s*([A-Za-z0-9_'\-]+)"
            players = re.findall(pattern, line, re.DOTALL)
        if players == []:
            pass
            # print("No matches found: ", line)
        elif players is not None and len(players) > 0:
            # print(players)
            for player in players:
                if player in full_player_list:
                    continue
                else:
                    full_player_list.append(player)

    print(full_player_list)

get_log_data()

