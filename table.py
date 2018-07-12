import logging
import json

from singleton import SingletonMetaclass
from player import Player


class Table(object):

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

    def find_player_by_md5(self, md5):
        for player in self.players:
            if player.md5 == md5:
                return player
        return None

    def find_player_by_name(self, name):
        for player in self.players:
            if player.real_name == name:
                return player
        return None

    def add_player_by_md5(self, md5_name):
        player = Player(md5=md5_name)
        self.players.append(player)
        logging.info("player (MD5(%s)) joined.", player.md5)
        return player

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

    def update_info(self, table_data):
        if self.number == int(table_data.data.table.tableNumber):
            self.round_name = table_data.data.table.roundName
            self.board = table_data.data.table.board
            self.round_count = table_data.data.table.roundCount
            self.raise_count = table_data.data.table.raiseCount
            self.bet_count = table_data.data.table.betCount
            self.small_blind = table_data.data.table.smallBlind
            self.big_blind = table_data.data.table.bigBlind
            logging.debug(vars(self))

            for player in table_data.data.players:
                new_player = self.find_player_by_md5(player.playerName)

                cards = None
                if hasattr(player, 'cards'):
                    cards = player.cards

                info = Player.PlayerInfo(player.playerName,
                                         player.chips,
                                         player.folded,
                                         player.allIn,
                                         player.isSurvive,
                                         player.reloadCount,
                                         player.roundBet,
                                         player.bet,
                                         cards)
                if new_player is not None:
                    new_player.update(info)
                else:
                    new_player = Player(info)
                    self.add_player(new_player)
                logging.debug(vars(new_player))

    def update_action(self, action):
        pass

    def update_winners(self, data):
        pass

    def end(self):
        pass


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