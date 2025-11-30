# Resolution and scaling system
BASE_WIDTH = 1500
BASE_HEIGHT = 750


"""Brand palette & typography helpers (IPSA / AMIS guideline)"""
# Primary brand colors
BLUE = (0x00, 0x5A, 0x9C)   # #005A9C Bleu foncé IPSA
LIGHT_BLUE   = (0x46, 0xB3, 0xE6)   # #46B3E6 Bleu clair AMIS
WHITE        = (0xFF, 0xFF, 0xFF)   # Blanc principal

# Supporting neutrals & semantic colors
NEUTRAL_LIGHT = (245, 247, 250)
NEUTRAL_BORDER = (215, 222, 230)
NEUTRAL_TEXT = (40, 55, 70)
NEUTRAL_SECONDARY = (95, 115, 135)
ERROR = (220, 60, 60)
WARNING = (250, 170, 40)
SUCCESS = (30, 150, 95)

# Mapped legacy names (maintain compatibility)

YELLOW = WARNING
RED = ERROR
GREEN = SUCCESS
BLACK = (10, 20, 30)  # Used sparingly for shadows / outlines
GRAY = NEUTRAL_BORDER
TEXT_PRIMARY = NEUTRAL_TEXT
TEXT_SECONDARY = NEUTRAL_SECONDARY
TEXT_MUTED = (140, 155, 170)

# Card / surfaces
CARD_BG = (120, 120, 120)  # Gris plus foncé
SURFACE = NEUTRAL_LIGHT

# Button pressed color (slightly darker primary)
BCP = (0, 74, 124)