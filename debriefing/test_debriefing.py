import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw

from debriefing.debriefing import (
    SQUAD_COLORS,
    create_image_summary,
    display_player_name,
    draw_card_background,
    get_json_kill_data,
    get_medal_data,
    resource_path,
)


class DebriefingDisplayTests(unittest.TestCase):
    def test_long_shot_excludes_support_without_affecting_other_medals(self):
        data = {
            "1": {
                "meta": {"playerName": "Support", "groupName": " support "},
                "combat": {"killsLongest": 2000, "grenadesThrown": 10},
            },
            "2": {
                "meta": {"playerName": "Other Support", "groupName": "Mascot"},
                "combat": {"killsLongest": 1500},
            },
            "3": {
                "meta": {"playerName": "Alpha", "groupName": "Alpha"},
                "combat": {"killsLongest": 500},
            },
            "4": {
                "meta": {"playerName": "Platoon", "groupName": '2nd Platoon - "Northstar"'},
                "combat": {"killsLongest": 600},
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertEqual(medals["Long Shot"]["name"], "Platoon")
            self.assertEqual(medals["Long Shot"]["value"], "600")
            self.assertEqual(medals["Grenadier"]["name"], "Support")

            data["3"]["combat"]["killsLongest"] = 300
            data["4"]["combat"]["killsLongest"] = 299
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(get_medal_data(str(path))["Long Shot"]["name"], "Alpha")
            data["3"]["combat"]["killsLongest"] = 299
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertNotIn("Long Shot", get_medal_data(str(path)))

            del data["3"]
            del data["4"]
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertNotIn("Long Shot", medals)
            self.assertEqual(medals["Grenadier"]["name"], "Support")

            data["3"] = {"meta": {"playerName": "Unknown"}, "combat": {"killsLongest": 400}}
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(get_medal_data(str(path))["Long Shot"]["name"], "Unknown")

    def test_grenadier_threshold_winner_and_ranking(self):
        data = {
            "1": {
                "meta": {"playerName": "Grenadier"},
                "combat": {"grenadesThrown": 10, "explosivesPlaced": 3},
            },
            "2": {
                "meta": {"playerName": "Other"},
                "combat": {"grenadesThrown": 5},
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertEqual(list(medals), ["Grenadier", "Demolition"])
            self.assertEqual(medals["Grenadier"]["name"], "Grenadier")
            self.assertEqual(medals["Grenadier"]["description"], "With 10 grenades thrown")
            data["1"]["combat"]["grenadesThrown"] = 4
            data["2"]["combat"]["grenadesThrown"] = 5
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(get_medal_data(str(path))["Grenadier"]["name"], "Other")
            data["2"]["combat"]["grenadesThrown"] = 4
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertNotIn("Grenadier", get_medal_data(str(path)))

    def test_engineering_medals_use_export_fields_and_thresholds(self):
        data = {
            "_mission": {"briefingName": "test_mission"},
            "1": {
                "meta": {"playerName": "Engineer"},
                "combat": {"explosivesDefused": 3, "explosivesPlaced": 7},
                "other": {"fortificationsBuilt": 3},
            },
            "2": {
                "meta": {"playerName": "Builder"},
                "combat": {"explosivesDefused": 2, "explosivesPlaced": 3},
                "other": {"fortificationsBuilt": 9},
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertEqual(medals["Bomb Disposal"]["name"], "Engineer")
            self.assertEqual(medals["Bomb Disposal"]["description"], "With 3 explosives defused")
            self.assertEqual(medals["Demolition"]["value"], "7")
            self.assertEqual(medals["Fort Builder"]["name"], "Builder")
            self.assertEqual(medals["Fort Builder"]["description"], "With 9 fortifications built")
            rendered_text = []
            original_text = ImageDraw.ImageDraw.text

            def capture_text(draw, xy, text, *args, **kwargs):
                rendered_text.append(text)
                return original_text(draw, xy, text, *args, **kwargs)

            with patch.object(ImageDraw.ImageDraw, "text", capture_text):
                create_image_summary(str(path), str(Path(temp_dir) / "output.png"))
            for name in ("Bomb Disposal", "Demolition", "Fort Builder"):
                self.assertIn(name, rendered_text)

            data["1"]["combat"] = {"explosivesDefused": 2, "explosivesPlaced": 2}
            data["2"]["combat"] = {}
            data["1"]["other"] = {"fortificationsBuilt": 2}
            data["2"]["other"] = {}
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            for name in ("Bomb Disposal", "Demolition", "Fort Builder"):
                self.assertNotIn(name, medals)

    def test_medals_are_ranked_by_target_ratio_before_limit(self):
        data = {
            "1": {
                "meta": {"playerName": "Player"},
                "combat": {
                    "killsLongest": 301, "killsDrones": 3, "killsArmored": 3,
                    "deaths": 4, "explosivesDefused": 3, "explosivesPlaced": 30,
                    "killsCivilian": 4,
                },
                "medical": {
                    "medicalBloodApplied": 2000, "medicalInjectionsRecieved": 15,
                    "unconsciousTime": 240, "unconsciousCount": 5,
                    "medicalBandagesRecieved": 30, "medicalAEDApplied": 50,
                    "woundsReceived": 31,
                },
                "other": {"fortificationsBuilt": 3},
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
        self.assertEqual(len(medals), 10)
        self.assertEqual(list(medals)[:2], ["Demolition", "War Criminal"])
        self.assertEqual(medals["Demolition"]["value"], "30")
        self.assertNotIn("Bomb Disposal", medals)
        self.assertNotIn("Fort Builder", medals)

    def test_ranking_ties_and_inclusive_thresholds(self):
        data = {
            "1": {
                "meta": {"playerName": "Player"},
                "medical": {"medicalBloodApplied": 16000, "medicalInjectionsRecieved": 30},
                "combat": {"killsLongest": 299, "killsCivilian": 0, "explosivesPlaced": 6},
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertEqual(list(medals), ["Blood Bank", "Pincushion", "Demolition"])
            data["1"]["combat"]["killsLongest"] = 300
            data["1"]["combat"]["killsCivilian"] = 2
            path.write_text(json.dumps(data), encoding="utf-8")
            medals = get_medal_data(str(path))
            self.assertEqual(list(medals)[:4], ["Blood Bank", "Pincushion", "War Criminal", "Demolition"])
            self.assertIn("Long Shot", medals)
            self.assertIn("War Criminal", medals)

    def test_previously_strict_medals_at_and_below_minimum(self):
        thresholds = (
            ("Long Shot", "combat", "killsLongest", 300),
            ("Bullet Magnet", "medical", "woundsReceived", 30),
            ("Death Wish", "combat", "deaths", 3),
            ("Vampire", "medical", "medicalBloodDrawnApplied", 1000),
            ("Sharpshooter", "combat", "hitHeadshots", 20),
            ("Trigger Happy", "combat", "firedCount", 500),
            ("War Criminal", "combat", "killsCivilian", 1),
            ("Human Colander", "medical", "totalBloodLoss", 8000),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            for name, category, key, minimum in thresholds:
                with self.subTest(medal=name):
                    data = {"1": {"meta": {"playerName": "Player"}, category: {key: minimum - 1}}}
                    path.write_text(json.dumps(data), encoding="utf-8")
                    self.assertNotIn(name, get_medal_data(str(path)))
                    data["1"][category][key] = minimum
                    path.write_text(json.dumps(data), encoding="utf-8")
                    self.assertIn(name, get_medal_data(str(path)))

    def test_card_has_translucent_dark_border_and_lighter_interior(self):
        image = Image.new("RGBA", (100, 100))
        draw_card_background(image, (10, 10, 90, 90))
        border = image.getpixel((12, 50))
        interior = image.getpixel((50, 50))
        self.assertTrue(0 < border[3] < 255)
        self.assertTrue(0 < interior[3] < 255)
        self.assertGreater(interior[0], border[0])

    def test_player_name_removes_tags_without_losing_other_name_parts(self):
        self.assertEqual(display_player_name("Player [AM2] [Alex]"), "Player")
        self.assertEqual(display_player_name("Player[AM] "), "Player")
        self.assertEqual(display_player_name("Player [AM2] (Alex)"), "Player (Alex)")
        self.assertEqual(display_player_name("Player [AM 2PS] (Alex)"), "Player (Alex)")
        self.assertEqual(display_player_name("[AM] Player"), "[AM] Player")
        self.assertEqual(display_player_name("Player [AM] Extra"), "Player Extra")
        self.assertEqual(display_player_name("Player [Other] Extra"), "Player [Other] Extra")
        self.assertEqual(display_player_name("[AM]"), "[AM]")

    def test_render_uses_clean_names_and_readable_squad_badges(self):
        data = {
            "_mission": {"briefingName": "test_mission"},
            "1": {
                "meta": {"playerName": "Alice [AM2] [Alex]", "groupName": "Alpha"},
                "combat": {"killsInfantry": 10},
                "medical": {"medicalBloodApplied": 8000},
            },
            "2": {
                "meta": {"playerName": "Bob [AM]", "groupName": '2nd Platoon - "Northstar"'},
                "combat": {"killsInfantry": 5},
            },
            "3": {
                "meta": {"playerName": "Charlie", "groupName": "Other"},
                "combat": {"killsInfantry": 1},
            },
        }
        texts = []
        rectangles = []
        original_text = ImageDraw.ImageDraw.text
        original_rectangle = ImageDraw.ImageDraw.rectangle

        def capture_text(draw, xy, text, *args, **kwargs):
            texts.append((xy, text, kwargs.get("fill")))
            return original_text(draw, xy, text, *args, **kwargs)

        def capture_rectangle(draw, xy, *args, **kwargs):
            rectangles.append((xy, kwargs.get("fill")))
            return original_rectangle(draw, xy, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            output_path = Path(temp_dir) / "output.png"
            input_path.write_text(json.dumps(data), encoding="utf-8")
            players = get_json_kill_data(str(input_path))
            self.assertIn("Alice [AM2] [Alex]", players)
            with patch.object(ImageDraw.ImageDraw, "text", capture_text), patch.object(
                ImageDraw.ImageDraw, "rectangle", capture_rectangle
            ):
                create_image_summary(str(input_path), str(output_path))
            with Image.open(output_path) as image:
                self.assertEqual(image.format, "PNG")
                with Image.open(resource_path("resources/templates/debriefing_template_medals.png")) as template:
                    for bounds in ((192, 403, 767, 427), (7, 95, 184, 111)):
                        self.assertIsNone(ImageChops.difference(
                            image.crop(bounds).convert("RGB"),
                            template.crop(bounds).convert("RGB"),
                        ).getbbox())

        self.assertIn(((270, 193), "Alice", (255, 255, 255)), texts)
        self.assertIn(((270, 213), "Bob", (255, 255, 255)), texts)
        self.assertTrue(any(text == "Alice" and xy[0] != 270 for xy, text, _ in texts))
        self.assertFalse(any(text == "Squad" for _, text, _ in texts))
        self.assertFalse(any(text in ("<", ">") for _, text, _ in texts))
        for y, name, color in (
            (193, "Alpha", SQUAD_COLORS["alpha"]),
            (213, "Platoon", SQUAD_COLORS["platoon"]),
            (233, "Support", SQUAD_COLORS["support"]),
        ):
            self.assertIn(((216, y), name, (245, 245, 245, 255)), texts)
            self.assertIn(((209, y - 5, 212, y + 5), color), rectangles)


if __name__ == "__main__":
    unittest.main()
