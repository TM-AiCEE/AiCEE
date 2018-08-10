DEBUG = False
TRAINING_MODE = True
TRAINING_SERVER_URL = r"ws://poker-training.vtr.trendnet.org:3001"
BATTLE_SERVER_URL = r"ws://poker-battle.vtr.trendnet.org:3001"
MAX_GAMES = 3
ALWAYS_FOLD = False
MAX_AMOUNT_CHIPS_ROUND = 320
bot_name = "186dd1804a914d93a44a601e582f2195"
LOG_FOLDER_NAME = "logs"
CHECK_STATUS_FILE = True

# pre-flop parameters
default_chips_rate = 0.1
default_thresholds = {
    "check": 0.15,
    "call": 0.20,
    "bet": 0.6,
    "raise": 0.8,
    "allin": 0.98,
    "chipsguard": 0.1
}
