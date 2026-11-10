import re
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import os

def draw_blurred_rectangle(base_img, xy, fill, outline, outline_width=2, blur_radius: float = 2):
    # Create a transparent layer
    temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    x0, y0, x1, y1 = xy

    # Draw outline (larger rectangle)
    for i in range(outline_width):
        draw.rectangle([x0 - i, y0 - i, x1 + i, y1 + i], fill=outline)
    # Draw filled rectangle
    draw.rectangle([x0, y0, x1, y1], fill=fill)

    # Apply blur to the whole temp image
    temp = temp.filter(ImageFilter.GaussianBlur(blur_radius))

    # Composite onto base image
    base_img.alpha_composite(temp)

def get_kill_data(file_path):
    with open(file_path, "r") as f:
        data = f.read()

    kill_data = {}
    mission_name = "unknown"
    map_name = "unknown"
    duration = 0

    # Use regex to find the mission name in the log file, which is usually in the format: mission="mission_name"
    mission_name_match = re.search(r'mission="([^"]+)"', data)
    if mission_name_match:
        mission_name = mission_name_match.group(1)
    else:
        return kill_data, "unknown", duration

    # Use regex to find the mission name in the log file, which is usually in the format: mission="mission_name"
    map_name_match = re.search(r'island="([^"]+)"', data)
    if map_name_match:
        map_name = map_name_match.group(1)
    else:
        return kill_data, "unknown", duration

    # Check if the mission name contains "training" (case-insensitive) and skip the log file if it does
    if "training" in mission_name.lower():
        return kill_data, "unknown", duration

    # Use regex to find the session time in the log file, which is usually in the format: duration=1213132123
    duration_match = re.search(r'duration=(\d+)', data)
    if duration_match:
        duration = int(duration_match.group(1))
        # Check if the session time is less than 30 minutes (1800 seconds) and skip the log file if it is
        if duration < 1800:
            return kill_data, "unknown", duration

    # Find each player and their kill counts using regex
    player_pattern = r'class\s+(\w+)\s*{([^}]*)};'
    players = re.findall(player_pattern, data, re.DOTALL)
    for player_index, player_data in players:
        name = re.search(r'name\s*=\s*"([^"]+)"\s*;', player_data)
        kills_inf = re.search(r'killsInfantry\s*=\s*(\d+);', player_data)
        kills_soft = re.search(r'killsSoft\s*=\s*(\d+);', player_data)
        kills_armored = re.search(r'killsArmor\s*=\s*(\d+);', player_data)
        kills_air = re.search(r'killsAir\s*=\s*(\d+);', player_data)
        total_score = re.search(r'killsTotal\s*=\s*(\d+);', player_data)
        total_deaths = re.search(r'killed\s*=\s*(\d+);', player_data)

        # Save total kills to json file
        player_data = {
            "name": name.group(1),
            "killsInfantry": int(kills_inf.group(1)) if kills_inf else 0,
            "killsSoft": int(kills_soft.group(1)) if kills_soft else 0,
            "killsArmor": int(kills_armored.group(1)) if kills_armored else 0,
            "killsAir": int(kills_air.group(1)) if kills_air else 0,
            "score": int(total_score.group(1)) if total_score else 0,
            "deaths": int(total_deaths.group(1)) if total_deaths else 0
        }

        #Skip headless clients
        if "headlessclient" in name.group(1):
            continue

        kill_data[name.group(1)] = player_data

    # Check if there are at least 10 players in the log file, if not, skip the log file
    if len(players) < 6:
        return {}, "unknown", duration

    return kill_data, map_name, duration * len(players)


combined_kill_data = {}
played_maps = {}
total_duration = 0

for log in os.listdir("history"):
    if log.endswith(".log"):
        kill_data, map_name, duration = get_kill_data(os.path.join("history", log))

        if map_name == "unknown":
            continue

        played_maps[map_name] = played_maps.get(map_name, 0) + 1
        total_duration += duration

        # Combine the kill data and aggregate the total kills for each player across all logs
        for player, data in kill_data.items():
            # Strip the player name of any [XXXX] tags and any leading or trailing whitespace
            renamed_player = re.sub(r'\[.*?\]', '', player).strip()
            data["name"] = renamed_player
            if renamed_player not in combined_kill_data:
                combined_kill_data[renamed_player] = data
                combined_kill_data[renamed_player]["operations_played"] = 1
            else:
                combined_kill_data[renamed_player]["killsInfantry"] += data["killsInfantry"]
                combined_kill_data[renamed_player]["killsSoft"] += data["killsSoft"]
                combined_kill_data[renamed_player]["killsArmor"] += data["killsArmor"]
                combined_kill_data[renamed_player]["killsAir"] += data["killsAir"]
                combined_kill_data[renamed_player]["score"] += data["score"]
                combined_kill_data[renamed_player]["deaths"] += data["deaths"]
                combined_kill_data[renamed_player]["operations_played"] += 1 # Ensure the name is updated to the stripped version



# Sort the combined kill data by score in descending order
combined_kill_data = dict(sorted(combined_kill_data.items(), key=lambda item: item[1]["score"], reverse=True))

# Save the combined kill data to a json file
with open("output/combined_kill_data.json", "w") as f:
    json.dump(combined_kill_data, f, indent=4)

with open("output/played_maps.json", "w") as f:
    json.dump(played_maps, f, indent=4)

# Print total maps played
total_maps_played = sum(played_maps.values())
print (f"Total maps played: {total_maps_played}")

# Load the debriefing template image
img = Image.open("resources/templates/debriefing_template_long.png").convert("RGBA")
img_draw = ImageDraw.Draw(img)

# Setup fonts
medium_title_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 16)
medium_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 13)
small_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 10)
tiny_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 9)
header_number_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 18)
header_number_font2 = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 16)
header_number_font3 = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 13)
mission_name_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 13)

# Setup the mission name at the top
mission_name_beautify = "AM2 Rewind 2026*"
img_draw.text((img.width // 2, 102), mission_name_beautify.upper(), fill=(255, 255, 255), font=mission_name_font, anchor="mm")
img_draw.text((img.width // 2, 1608), "* but actually this is from March onwards, excludes training missions and only extracts data from operation servers only", fill=(155, 155, 155), font=small_body_font, anchor="mm")

# # Setup most used weapon
# img_draw.text((img.width - 864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")
# # Setup medal titles
# img_draw.text((864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")

#####################################

# Get the total kills and civilian casualties
kill_data = combined_kill_data
total_kills = sum(player["killsInfantry"] for player in kill_data.values())
total_deaths = sum(player["deaths"] for player in kill_data.values())

# Draw the total kills, deaths, and civilian casualties at the top of the image
img_kills = Image.new('RGBA', img.size, (255, 255, 255, 0))
img_kills_draw = ImageDraw.Draw(img_kills)
img_kills_draw.text((372, 132), f"{total_kills}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
img_kills_draw.text((563, 132), f"{total_deaths}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
img_kills_draw.text((753, 132), f"{round(total_duration/60/60)}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")

# Player stats header
player_spacing = 61
img_kills_draw.text((209, 170), "#", fill=(255, 255, 255), font=medium_body_font, anchor="mm")
img_kills_draw.text((219, 170), "Name", fill=(255, 255, 255), font=medium_title_font, anchor="lm")
img_kills_draw.text((338 + (player_spacing * 0), 170), "Infantry", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((338 + (player_spacing * 1), 170), "Light", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((338 + (player_spacing * 2), 170), "Armored", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((338 + (player_spacing * 3), 170), "Air", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((338 + (player_spacing * 4), 170), "Deaths", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((338 + (player_spacing * 5), 170), "Score", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
img_kills_draw.text((347 + (player_spacing * 6), 170), "Operations", fill=(255, 255, 255), font=medium_title_font, anchor="mm")

# List each player's stats
for player in kill_data:

    pdata = kill_data[player]
    index = list(kill_data.keys()).index(player)
    if index >= 69:
        break
    y_position = 193 + index * 20

    if index % 2 == 0:
        draw_blurred_rectangle(img_kills, (200 + 1, y_position - 9, 200 + 560 - 2, y_position + 10), fill=(220, 220, 220, 10), outline=(0, 0, 0, 40), outline_width=1, blur_radius=0.6)

    draw_blurred_rectangle(img_kills, (200 + 1, y_position - 10, 200 + 560 - 2, y_position - 9), fill=(250, 250, 250, 10), outline=(0, 0, 0, 0), outline_width=0, blur_radius=0)

    img_kills_draw.text((209, y_position + 1), str(index + 1), fill=(60, 60, 60, 120), font=tiny_body_font, anchor="mm")
    img_kills_draw.text((217, y_position), pdata["name"], fill=(255, 255, 255), font=medium_body_font, anchor="lm")
    img_kills_draw.text((338 + (player_spacing * 0), y_position), str(pdata["killsInfantry"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((338 + (player_spacing * 1), y_position), str(pdata["killsSoft"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((338 + (player_spacing * 2), y_position), str(pdata["killsArmor"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((338 + (player_spacing * 3), y_position), str(pdata["killsAir"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((338 + (player_spacing * 4), y_position), str(pdata["deaths"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((338 + (player_spacing * 5), y_position), str(pdata["score"]), fill=(255, 255, 0, 200), font=medium_body_font, anchor="mm")
    img_kills_draw.text((344 + (player_spacing * 6), y_position), str(pdata["operations_played"]), fill=(255, 255, 255, 200), font=medium_body_font, anchor="mm")

# Composite the kills and medals onto the main image
img = Image.alpha_composite(img, img_kills)

##############################

# Custom medals
medal_data = {}

support_players = ["TheDaveinator","TimHawk","Flay","Chris","Wer","Flay","DustyEllis"]
kill_data_filtered = {k: v for k, v in kill_data.items() if k not in support_players}
kill_data_support = {k: v for k, v in kill_data.items() if k in support_players}

#Get the player with the most deaths
highest_deaths_player = max(kill_data.items(), key=lambda x: x[1]["deaths"])[0]
death_award_medal = {"medal": "Darwin Award", "name": highest_deaths_player, "value": str(kill_data[highest_deaths_player]["deaths"]), "description": f"With {kill_data[highest_deaths_player]['deaths']} deaths", "image_path": "resources/medals/medal_generic.png"}
medal_data["Darwin Award"] = death_award_medal

# Get the player with the most operations attended
highest_operations_player = max(kill_data.items(), key=lambda x: x[1]["operations_played"])[0]
operations_award_medal = {"medal": "Eternal Warrior", "name": highest_operations_player, "value": str(kill_data[highest_operations_player]["operations_played"]), "description": f"With {kill_data[highest_operations_player]['operations_played']} operations attended", "image_path": "resources/medals/medal_generic.png"}
medal_data["Eternal Warrior"] = operations_award_medal

##SUPPORT EXCLUSIONS
# Get the player with the most kills excluding support players
highest_kills_player = max(kill_data_filtered.items(), key=lambda x: x[1]["killsInfantry"])[0]
highest_kills_medal = {"medal": "Top Gun", "name": highest_kills_player, "value": str(kill_data[highest_kills_player]["score"]), "description": f"With {kill_data[highest_kills_player]['killsInfantry']} kills as infantry", "image_path": "resources/medals/medal_generic.png"}
medal_data["Top Gun"] = highest_kills_medal

# Get the player with most armored kills excluding support players
highest_armored_kills_player = max(kill_data_filtered.items(), key=lambda x: x[1]["killsArmor"])[0]
highest_armored_kills_medal = {"medal": "Tank Buster", "name": highest_armored_kills_player, "value": str(kill_data[highest_armored_kills_player]["killsArmor"]), "description": f"With {kill_data[highest_armored_kills_player]['killsArmor']} armored kills as infantry", "image_path": "resources/medals/medal_generic.png"}
medal_data["Tank Buster"] = highest_armored_kills_medal

# Get the player with most air kills excluding support players
highest_air_kills_player = max(kill_data_filtered.items(), key=lambda x: x[1]["killsAir"])[0]
highest_air_kills_medal = {"medal": "Sky Hunter", "name": highest_air_kills_player, "value": str(kill_data[highest_air_kills_player]["killsAir"]), "description": f"With {kill_data[highest_air_kills_player]['killsAir']} air kills as infantry", "image_path": "resources/medals/medal_generic.png"}
medal_data["Sky Hunter"] = highest_air_kills_medal

# Get the highest kill/death ratio player excluding support players
highest_kd_player = max(kill_data_filtered.items(), key=lambda x: (x[1]["killsInfantry"] / x[1]["deaths"]) if x[1]["deaths"] > 0 else 0)[0]
highest_kd_medal = {"medal": "'Elite' Operator", "name": highest_kd_player, "value": str(round(kill_data[highest_kd_player]["killsInfantry"] / kill_data[highest_kd_player]["deaths"], 2)) if kill_data[highest_kd_player]["deaths"] > 0 else "N/A", "description": f"With a K/D ratio of {round(kill_data[highest_kd_player]['killsInfantry'] / kill_data[highest_kd_player]['deaths'], 2) if kill_data[highest_kd_player]['deaths'] > 0 else 'N/A'}", "image_path": "resources/medals/medal_generic.png"}
medal_data["KD"] = highest_kd_medal

# Get the highest score per player / operations played excluding support players
highest_score_per_operation_player = max(kill_data_filtered.items(), key=lambda x: (x[1]["score"] / x[1]["operations_played"]) if x[1]["operations_played"] > 0 else 0)[0]
highest_score_per_operation_medal = {"medal": "Consistent Performer", "name": highest_score_per_operation_player, "value": str(round(kill_data[highest_score_per_operation_player]["score"] / kill_data[highest_score_per_operation_player]["operations_played"], 2)) if kill_data[highest_score_per_operation_player]["operations_played"] > 0 else "N/A", "description": f"With an average score of {round(kill_data[highest_score_per_operation_player]['score'] / kill_data[highest_score_per_operation_player]['operations_played'], 2) if kill_data[highest_score_per_operation_player]['operations_played'] > 0 else 'N/A'} per op", "image_path": "resources/medals/medal_generic.png"}
medal_data["Consistent Performer"] = highest_score_per_operation_medal

##SUPPORT ONLY
# Get the support player with the most air kills
highest_air_to_air_kills_player = max(kill_data_support.items(), key=lambda x: x[1]["killsAir"])[0]
highest_air_to_air_kills_medal = {"medal": "Air Superiority", "name": highest_air_to_air_kills_player, "value": str(kill_data_support[highest_air_to_air_kills_player]["killsAir"]), "description": f"With {kill_data_support[highest_air_to_air_kills_player]['killsAir']} air kills as support", "image_path": "resources/medals/medal_generic.png"}
medal_data["Air Superiority"] = highest_air_to_air_kills_medal

# Get score of the support player with the most score
guardian_angel_player = max(kill_data_support.items(), key=lambda x: x[1]["score"])[0]
guardian_angel_medal = {"medal": "Guardian Angel", "name": guardian_angel_player, "value": str(kill_data_support[guardian_angel_player]["score"]), "description": f"With {kill_data_support[guardian_angel_player]['score']} score as support", "image_path": "resources/medals/medal_generic.png"}
medal_data["Guardian Angel"] = guardian_angel_medal

# Get the support player with the most deaths
highest_support_deaths_player = max(kill_data_support.items(), key=lambda x: x[1]["deaths"])[0]
highest_support_deaths_medal = {"medal": "Asset Burner", "name": highest_support_deaths_player, "value": str(kill_data_support[highest_support_deaths_player]["deaths"]), "description": f"With {kill_data_support[highest_support_deaths_player]['deaths']} support assets lost", "image_path": "resources/medals/medal_generic.png"}
medal_data["Asset Burner"] = highest_support_deaths_medal

img_medals = Image.new('RGBA', img.size, (0, 0, 0, 0))
img_medals_draw = ImageDraw.Draw(img_medals)

def draw_medal_container(image, medal=None, position=(0, 0), size=(178, 72)):
    draw_blurred_rectangle(image, (position[0], position[1], position[0] + size[0], position[1] + size[1]), fill=(0, 0, 0, 170), outline=(0, 0, 0, 40), outline_width=1, blur_radius=0.6)
    draw_blurred_rectangle(image, (position[0] + 6, position[1] + 6, position[0] + size[0] - 6, position[1] + size[1] - 6), fill=(121, 121, 121, 28), outline=(0, 0, 0, 60), outline_width=1, blur_radius=0.6)
    if medal is not None:
        # Draw transparent medal image
        try:
            medal_img = Image.open(medal["image_path"]).convert("RGBA").resize((size[1] - 18, size[1] - 18))
            image.paste(medal_img, (position[0] + (size[0] // 2) - ((size[1] - 18) // 2), position[1] + (size[1] // 2) - ((size[1] - 18) // 2)), medal_img)
        except Exception as e:
            print(f"Error loading medal image: {e}")
        # Draw medal information
        if len(medal["medal"]) > 18:
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) - 14), str(medal["medal"]).upper(), fill=(255, 255, 255), font=header_number_font3, anchor="mm")
        elif len(medal["medal"]) > 14:
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) - 14), str(medal["medal"]).upper(), fill=(255, 255, 255), font=header_number_font2, anchor="mm")
        else:
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) - 14), str(medal["medal"]).upper(), fill=(255, 255, 255), font=header_number_font, anchor="mm")
        img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) + 4), str(medal["name"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) + 18), str(medal["description"]), fill=(255, 255, 255, 100), font=small_body_font, anchor="mm")


for medal in medal_data:
    mdata = medal_data[medal]
    index = list(medal_data.keys()).index(medal)
    if index < 10:
        draw_medal_container(img_medals, medal=mdata, position=(7, 113 + (index * (72 + 4))))
    elif index < 20:
        draw_medal_container(img_medals, medal=mdata, position=(775, 113 + ((index - 10) * (72 + 4))))
    else:
        pass

# Composite the kills and medals onto the main image
img = Image.alpha_composite(img, img_medals)



##################################


img_other = Image.new('RGBA', img.size, (0, 0, 0, 0))
img_other_draw = ImageDraw.Draw(img_other)
size = (178, 400)

draw_blurred_rectangle(img_other, (775, 113, 775 + size[0], 113 + size[1]), fill=(0, 0, 0, 170), outline=(0, 0, 0, 40), outline_width=1, blur_radius=0.6)
draw_blurred_rectangle(img_other, (775 + 6, 113 + 6, 775 + size[0] - 6, 113 + size[1] - 6), fill=(121, 121, 121, 28), outline=(0, 0, 0, 60), outline_width=1, blur_radius=0.6)
img_other_draw.text((775 + (size[0] // 2), 113 + 20), "FAVOURITE MAPS", fill=(255, 255, 255), font=header_number_font, anchor="mm")


img = Image.alpha_composite(img, img_other)


##############################

# Save and show the image
img.save(f'output/am2_rewind_2025.png')
img.show()