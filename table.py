import logging
import json
import settings

from singleton import SingletonMetaclass
from player import Player, Bot
from operator import attrgetter
from enum import Enum
from plugins.treys import Card

class Table(object):

    stages_name = ["Deal", "Flop", "Turn", "River"]

    class STAGE(Enum):
        Preflop = 0
        Flop = 1
        Turn = 2
        River = 3

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

        # customize for statistics
        self._survive_player_num = 0
        self._winners = []
        self._mine = None

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

        # customize for statistics
        self._survive_player_num = 0
        self._winners.clear()

    def find_player_by_md5(self, md5):
        for player in self.players:
            if player.md5 == md5:
                return player
        return None

    def get_bot_by_name(self, name):
        for player in self.players:
            if type(player) is Bot and player.md5 == name:
                return player
        return None

    def add_player_by_md5(self, md5_name):
        player = self.find_player_by_md5(md5_name)
        if player is None:
            player = Player(md5=md5_name)
            self.players.append(player)

    def set_bot(self, player):
        self._mine = player

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

    def new_round(self):
        logging.info("========== new round ========")

    def end_round(self):
        # calculate survive players
        total_chips = 0
        for player in self.players:
            if player.is_survive:
                self._survive_player_num += 1
                total_chips += player.chips

        # list players chips rank
        win_money = 0
        message, card, rank = "", "", ""

        ranks = sorted(self.players, key=attrgetter('chips'), reverse=True)
        for index, player in enumerate(ranks):

            if hasattr(player, 'win_money'):
                win_money = player.win_money

            # end of round
            if hasattr(player, 'hand'):
                message = player.hand.message
                card = player.hand.cards
                rank = player.hand.rank

            if type(player) is Bot:
                logging.info("[AiCEE] [%2s] player %s, chips %5s (%3f), %s (%16s)(%4d), win_money: %5s",
                             (index+1), player.md5[:5], player.chips, player.chips/total_chips,
                             card, message, rank, win_money)
            else:
                logging.info("[OTHER] [%2s] player %s, chips %5s (%3f), %s (%16s)(%4d), win_money: %5s",
                             (index+1), player.md5[:5], player.chips, player.chips/total_chips,
                             card, message, rank, win_money)

    #
    # __show_action
    #
    def update_action(self, action):

        for player in self.players:
            if player.allin and player.is_survive:
                logging.info("[%5s] player name: %s, chips: %5s, all in: %s",
                             self.round_name, player.md5[:5], player.chips, player.allin)

        if hasattr(action, "amount"):
            logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d",
                         self.round_name, action.playerName[:5], action.action, action.amount, action.chips, self.total_bet)
        else:
            logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d",
                         self.round_name, action.playerName[:5], action.action, 0, action.chips, self.total_bet)

    def update_winners_info(self, winners):
        for winner in winners:
            self._winners.append(winner)
            player = self.get_bot_by_name(settings.bot_name)
            if player and player.md5 == winner.playerName:
                logging.info("[AiCEE] The winner is (%s)-(%s), chips:(%5s)",
                             winner.playerName, winner.hand.message, winner.chips)
            else:
                logging.info("[OTHER] The winner is (%s)-(%s), chips:(%5s)",
                             winner.playerName, winner.hand.message, winner.chips)

    def game_over(self):
        if self._mine is not None:
            self._mine.join()

    def get_survive_player_num(self):
        return self._survive_player_num

    def has_allin(self):
        someone_allin = False
        for player in self.players:
            if player.allin and player.is_survive:
                someone_allin = True
        return someone_allin

    def total_chips(self):
        total_chips = 0
        for player in self.players:
            total_chips += player.chips
        return total_chips


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