import logging
import sys

from singleton import SingletonMetaclass
from player import Player, PlayerAction, Bot
from operator import attrgetter
from plugins.evaluation.handevaluator import HandEvaluator


class Table(object):

    # round name: Deal(pre-flop, flop, turn, river)
    # small/big blind: playerName, amount
    # total bet: only update game board information
    def __init__(self, client, number, status):
        self.number = number
        self.status = status
        self.round_name = ""
        self.board = list()
        self.round_count = 0
        self.raise_count = 0
        self.bet_count = 0
        self.small_blind = dict()
        self.big_blind = dict()
        self.players = list()

        self.total_bet = 0
        self.init_chips = 0
        self.max_reload_count = 0

        self._client = client
        self._evaluator = HandEvaluator()
        self._mine = None

        # customize for statistics
        self._actions = list()
        self._winners = list()
        self._win = False
        self._current_amount = 0

    def _reset(self):
        self.round_name = ""
        self.board.clear()
        self.round_count = 0
        self.raise_count = 0
        self.bet_count = 0
        self.small_blind.clear()
        self.big_blind.clear()
        self.players.clear()
        self.total_bet = 0
        self.init_chips = 0
        self.max_reload_count = 0

        # customize for statistics
        self._winners.clear()
        self._win = False
        self._current_amount = 0
        self._actions.clear()

    def find_player(self, md5):
        for player in self.players:
            if player.md5 == md5:
                return player
        return None

    def add_player_by_md5(self, md5_name):
        player = self.find_player(md5_name)
        if player is None:
            player = Player(md5=md5_name)
            self.players.append(player)

    def add_player_by_obj(self, player):
        if type(player) is Bot:
            self._mine = player
            self.players.append(player)
            logging.info("player MD5(%s) joined.", player.md5)
        else:
            raise sys.exit("[add_player_by_obj]")

    def bot(self):
        return self._mine

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

        # update game board information
        if hasattr(data, "totalBet"):
            self.total_bet = data.totalBet

    def update_players(self, players):
        for pjson in players:
            player = self.find_player(pjson.playerName)
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
                if hasattr(pjson, 'roundBet'):
                    info.round_bet = pjson.roundBet

                if hasattr(pjson, 'bet'):
                    info.bet = pjson.bet

                if hasattr(pjson, 'hand'):
                    info.hand = pjson.hand
                    info.cards = pjson.hand.cards

                if hasattr(pjson, 'winMoney'):
                    info.win_money = pjson.winMoney
                    player.is_online = pjson.isOnline

                player.update(info)

    def new_round(self):
        logging.info("========== new round (%s) ========", self.round_count)

    def end_round(self):

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
                card = self._evaluator.print_pretty_cards(player.hand.cards)
                rank = player.hand.rank

            total_chips = self.total_chips()
            if player.md5 == self.bot().md5:
                logging.info("[AiCEE] [%2s] player %s, chips %5s (%3f), %s (%16s)(%4d), win_money: %5s",
                             (index+1), player.md5[:5], player.chips, player.chips/total_chips,
                             card, message, rank, win_money)
            else:
                logging.info("[OTHER] [%2s] player %s, chips %5s (%3f), %s (%16s)(%4d), win_money: %5s",
                             (index+1), player.md5[:5], player.chips, player.chips/total_chips,
                             card, message, rank, win_money)

        # clear cards for each player
        for player in self.players:
            player.cards.clear()

        # clear board cards
        self.board.clear()

    def update_action(self, json_act):

        amount = 0
        if hasattr(json_act, "amount"):
            amount = int(json_act.amount)

        act = PlayerAction(json_act.action, json_act.playerName, amount, json_act.chips)
        self._actions.append(act)

    def show_action(self):

        act = self._actions.pop(0)

        if act.act == "allin":
            logging.info("[%5s] player name: %s, chips: %5s, amount: %s",
                         self.round_name, act.md5[:5], act.chips, act.amount)

        logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d",
                     self.round_name, act.md5[:5], act.act, act.amount, act.chips, self.total_bet)

    def update_winners_info(self, winners):
        for winner in winners:
            self._winners.append(winner)

            if winner.playerName == self.bot().md5:
                self._win = True
                logging.info("[AiCEE] The winner is (%s)-(%16s), chips:(%5s)",
                             winner.playerName[:5], winner.hand.message, winner.chips)
            else:
                logging.info("[OTHER] The winner is (%s)-(%16s), chips:(%5s)",
                             winner.playerName[:5], winner.hand.message, winner.chips)

    def game_over(self):

        md5 = self._mine.md5

        self.players.clear()
        self._winners.clear()
        self._client.reconnect()

        # if not self._win:
        #    reconnect_time = 30
        #    time.sleep(reconnect_time)
        #    self._client.reconnect()
        #    logging.info("[game_over] wait for reconnecting server after %s secs.", reconnect_time)

        # player = Bot(self._client, md5)
        # player.join()
        # self.add_player_by_obj(player)

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
        self.tables = list()

    def create(self, client, number=0, status=0):
        table = Table(client, number, status)
        self.tables.append(table)
        return table

    def current(self):
        if len(self.tables) < 0:
            raise sys.exit("Creating table object before joining to server is necessary.")

        return self.tables[0]
