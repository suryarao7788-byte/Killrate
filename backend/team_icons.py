"""
team_icons.py
-------------
Maps ktdash killteamName → local icon filename.
Icons live in the icons/ subfolder.
"""

import os

# Maps exact ktdash killteamName to icon filename in icons/
TEAM_ICON_FILES: dict[str, str] = {
    "Angels Of Death":          "Angels of Death.jpg",
    "Battleclade":              "Battleclade.jpg",
    "Blades Of Khaine":         "Blades of Khaine.jpg",
    "Blooded":                  "Blooded.jpg",
    "Brood Brothers":           "Brood Brothers.jpg",
    "Canoptek Circle":          "Canoptek Circle.jpg",
    "Celestian Insidiants":    "Celestinian Insidants.jpg",
    "Chaos Cult":               "Chaos Cult.jpg",
    "Corsair Voidscarred":      "Corsair Voidscarred.jpg",
    "Death Korps":              "Death Korps.jpg",
    "Deathwatch":               "Deathwatch.jpg",
    "Elucidian Starstriders":   "Elucidian Starstriders.jpg",
    "Exaction Squad":           "Exaction Squad.webp",
    "Farstalker Kinband":       "Farstalker Kinband.jpg",
    "Fellgor Ravagers":         "Fellgor Ravagers.jpg",
    "Gellerpox Infected":       "Gellerpox Infected.jpg",
    "Goremongers":              "Goremongers.jpg",
    "Hand Of The Archon":       "Hand of the Archon.jpg",
    "Hearthkyn Salvagers":      "Hearthkyn Salvagers.jpg",
    "Hernkyn Yaegirs":          "Hernkyn Yaegirs.jpg",
    "Hierotek Circle":          "Hierotek Circle.jpg",
    "Hunter Clade":             "Hunterclade.jpg",
    "Imperial Navy Breachers":  "Imperial Navy Breachers.jpg",
    "Inquisitorial Agents":     "Inquisitorial Agents.jpg",
    "Kasrkin":                  "Kasrkin.jpg",
    "Kommandos":                "Kommandos.jpg",
    "Legionaries":              "Legionnaires.jpg",
    "Mandrakes":                "Mandrakes.jpg",
    "Murderwing":               "Murderwing.jpg",
    "Nemesis Claw":             "Nemesis Claw.jpg",
    "Novitiates":               "Novitiates.jpg",
    "Pathfinders":             "pathfinders.jpg",
    "Phobos Strike Team":       "Phobos Strike Team.jpg",
    "Plague Marines":          "Plague Marines.jpg",
    "Ratlings":                 "Ratlings.jpg",
    "Raveners":                 "Raveners.jpg",
    "Sanctifiers":              "Sanctifiers.jpg",
    "Scout Squad":             "Scout Squad.jpg",   # note: typo in filename preserved
    "Tempestus Aquilon":       "Tempestus Aquilons.jpg",
    "Vespid Stingwings":        "Vespid Stingwings.jpg",
    "Void-Dancer Troupe":       "Void-Dancer Troupe.jpg",
    "Warp Coven":              "Warp Coven.jpg",
    "Wolf Scouts":              "Wolf Scouts.jpg",
    "Wrecka Krew":              "Wrecka Krew.jpg",
    "Wyrmblade":                "Wyrmblade.jpg",
    "XV26 Stealth Battlesuits":"XV25 Stealth Suit.jpg",
}

ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")


def get_icon_path(team_name: str) -> str | None:
    """Return absolute path to the icon file, or None if not found."""
    filename = TEAM_ICON_FILES.get(team_name)
    if not filename:
        return None
    path = os.path.join(ICONS_DIR, filename)
    return path if os.path.exists(path) else None


def get_icon(team_name: str) -> str:
    """Fallback emoji for teams without an image."""
    return "⚔️"
