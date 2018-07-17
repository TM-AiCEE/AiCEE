import logging
import json
import settings

from singleton import SingletonMetaclass
from player import Player, Bot
from operator import attrgetter

class Table(object):

    stages = ["Deal", "Flop", "Turn", "River"]

    def __init__(self, client=None, number=5274, status=0):
        self.client = client
        self.number = number
        self.status = status
        self.round_name = ""
        self.board = []
        self.round_count = 0
        self.raise_count = 0
        self.bet_count = 0
        self.small_blind = None
        self.big_blind = None
        self.players = []
        self.total_bet = None
        self.init_chips = 0
        self.max_reload_count = 0
        self._survive_player_num = 0

    def _reset(self):
        self.round_name = ""
        self.board.clear()
        self.round_count = 0
        self.raise_count = 0
        self.bet_count = 0
        self.small_blind = None
        self.big_blind = None
        self.players.clear()
        self.total_bet = None
        self.init_chips = 0
        self.max_reload_count = 0
        self._survive_player_num = 0

    def find_player_by_md5(self, md5):
        for player in self.players:
            if player.md5 == md5:
                return player
        return None

    def find_player_by_name(self, name):
        for player in self.players:
            if player.md5 == name:
                return player
        return None

    def add_player_by_md5(self, md5_name):
        player = self.find_player_by_md5(md5_name)
        if player is None:
            player = Player(md5=md5_name)
            self.players.append(player)

    def add_player(self, player):
        self.players.append(player)
        logging.info("player (MD5(%s)) joined.", player.md5)

    def update_players(self, players):
        for pjson in players:
            player = self.find_player_by_md5(pjson.playerName)
            if player:
                cards = None

                if hasattr(pjson, 'cards'):
                    cards = pjson.cards

                info = Player.PlayerInfo(pjson.playerName,
                                         pjson.chips,
                                         pjson.folded,
                                         pjson.allIn,
                                         pjson.isSurvive,
                                         pjson.reloadCount,
                                         pjson.roundBet,
                                         pjson.bet,
                                         cards)
                # end of round
                if hasattr(pjson, 'hand'):
                    info.hand = pjson.hand
                    info.cards = pjson.hand.cards

                if hasattr(pjson, 'winMoney'):
                    info.win_money = pjson.winMoney
                    player.is_online = pjson.isOnline

                # end of round

                player.update(info)

    def update_table(self, data):
        self.board = data.board
        self.round_count = data.roundCount
        self.raise_count = data.raiseCount
        self.bet_count = data.betCount
        self.round_name = data.roundName
        self.small_blind = data.smallBlind
        self.big_blind = data.bigBlind

        if hasattr(data, "maxReloadCount"):
            self.max_reload_count = data.maxReloadCount

        if hasattr(data, "initChips"):
            self.init_chips = data.initChips

        if hasattr(data, "status"):
            self.status = data.status

        if hasattr(data, "totalBet"):
            self.total_bet = data.totalBet

    def end_round(self):
        # show all player chips
        for player in self.players:
            if type(player) is Bot:
                logging.info("[AiCEE] player name: %s, chips: %d, is_survive: %s, is_human=%s.", player.md5, player.chips, player.is_survive, player.is_human)
            else:
                logging.info("[OTHER] player name: %s, chips: %d, is_survive: %s, is_human=%s.", player.md5, player.chips, player.is_survive, player.is_human)

        self._survive_player_num = len(self.players) + 1
        for player in self.players:
            if not player.is_survive:
                self._survive_player_num -= 1

        # list players chips rank
        ranks = sorted(self.players, key=attrgetter('chips'), reverse=True)
        for index, player in enumerate(ranks):
            if type(player) is Bot:
                logging.info("[AiCEE] [%s] current player %s by chips %s. ", (index+1), player.md5, player.chips)
            else:
                logging.info("[OTHER] [%s] current player %s rank by chips %s", (index+1), player.md5, player.chips)


    def update_action(self, action):
        someone_all_in = False
        for player in self.players:
            if player.allin:
                logging.info("player name: %s, chips: %s, all in: %s", player.md5, player.chips, player.allin)
                someone_all_in = True
        if hasattr(action, "amount"):
            logging.info("player name: %s, action: %s, amount:%s, chips: %s",
                     action.playerName, action.action, action.amount, action.chips)
        else:
            logging.info("player name: %s, action: %s, amount:%s, chips: %s",
                         action.playerName, action.action, 0, action.chips)

    def update_winners(self, winners):
        for winner in winners:
            logging.debug("The winner is (%s)-(%s), chips:(%s)", winner.playerName, winner.hand.message, winner.chips)

    def end(self):
        player = self.find_player_by_name(settings.bot_name)
        if type(player) is Bot:
            player.join()
        self._reset()

    def get_survive_player_num(self):
        return self._survive_player_num


class TableManager(metaclass=SingletonMetaclass):
    def __init__(self):
        self.tables = []

    def _add_table(self, table):
        self.tables.append(table)

    def set_table(self, number, status):
        table = Table(number=number, status=status)
        self._add_table(table)
        return table

    def get_table(self, number):
        return self.tables[0]

    def current(self):
        return self.tables[0]