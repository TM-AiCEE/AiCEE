import logging
import sys
import time
import random
import datetime
import settings
import utils
import os
import display_name

from termcolor import colored
from singleton import SingletonMetaclass
from player import Player, PlayerAction, Bot
from operator import attrgetter
from handevaluator import HandEvaluator


class Table(object):

    # round name: Deal(pre-flop, flop, turn, river)
    # small/big blind: playerName, amount
    # total bet: only update game board information
    def __init__(self, client, number, status):
        self.number = number
        self.status = status
        self.round_name = ""
        self.board = list()
        self.round_count = -1
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
        self.player_actions = list()
        self._winners = list()
        self._win = False
        self._current_amount = 0
        self._total_count = 0
        self._win_count = 0
        self._chips = 0
        self._player_games = 1
        self.current_round = ""
        self.bet_big_chips = False

    def _reset(self):
        self.round_name = ""
        self.board.clear()
        self.round_count = -1
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
        self.player_actions.clear()

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

        # clear all actions of players history
        self.player_actions.clear()

        # list big-blind and small-blind players
        if len(self.big_blind) > 0 and len(self.small_blind) > 0:
            logging.info("[%5s] Big-Blind: (%s), bet:(%s), Small-Blind: (%s), bet:(%s)",
                         self.round_name,
                         self.big_blind.playerName[:5], self.big_blind.amount,
                         self.small_blind.playerName[:5], self.small_blind.amount)

    def end_round(self):

        # list players chips rank
        win_money = 0
        message, card, rank = "", "", ""

        ranks = sorted(self.players, key=attrgetter('chips'), reverse=True)
        for index, player in enumerate(ranks):

            if hasattr(player, 'win_money'):
                win_money = player.win_money

            # end of round
            if hasattr(player, 'hand') and hasattr(player.hand, 'message'):
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

        fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.txt")
        if settings.CHECK_STATUS_FILE and os.path.isfile(fname):
            os.remove(fname)
            utils.restart_program()

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
        self.player_actions.append(act)

        if act.act == 'bet' and act.chips >= self._mine.chips:
            self.bet_big_chips = True
            self.current_round = self.round_name
            logging.info("[update actions] %s bet big amount. %s. chip_rate: %s",
                         act.md5[:5], act.amount, act.amount/act.chips)

        if self.current_round != self.round_name:
            self.bet_big_chips = False

    def show_action(self):

        act = self.player_actions[-1]

        if self.is_big_blind_player(act.md5):
            c_bigblind = colored("Big-Blind", 'magenta')

            if act.md5 == self._mine.md5:
                c_act = colored(act.act, 'yellow')
            else:
                c_act = act.act

            logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d. (%s)",
                         self.round_name, act.md5[:5], c_act, act.amount, act.chips, self.total_bet, c_bigblind)

        elif self.is_small_blind_player(act.md5):
            c_bigblind = colored("Small-Blind", 'magenta')

            if act.md5 == self._mine.md5:
                c_act = colored(act.act, 'yellow')
            else:
                c_act = act.act

            logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d. (%s)",
                         self.round_name, act.md5[:5], c_act, act.amount, act.chips, self.total_bet, c_bigblind)
        else:

            if act.md5 == self._mine.md5:
                c_act = colored(act.act, 'yellow')
            else:
                c_act = act.act

            logging.info("[%5s] player name: %s, action: %5s, amount:%4s, chips: %5s, total bet: %4d.",
                         self.round_name, act.md5[:5], c_act, act.amount, act.chips, self.total_bet)

    def update_winners_info(self, winners):
        for winner in winners:
            self._winners.append(winner)

            if winner.playerName == self.bot().md5:
                self._win = True
                self._win_count += 1
                self._chips += winner.chips
                logging.info("[AiCEE] The winner is (%s)-(%16s), chips:(%5s)",
                             winner.playerName[:5], winner.hand.message, winner.chips)
            else:
                logging.info("[OTHER] The winner is (%s)-(%16s), chips:(%5s)",
                             winner.playerName[:5], winner.hand.message, winner.chips)

    def summarize(self):
        logging.info("[summaries] total played: %s, win rate: %s, chips: %s",
                     self._total_count,
                     self._win_count / self._total_count,
                     self._chips)
        self._save_summarize()

    def game_over(self):

        self._total_count += 1
        self._winners.clear()
        self.summarize()

        if not self._win:
            reconnect_time = random.randrange(30, 60)
            logging.info("[game_over] wait for reconnecting server after %s secs.", reconnect_time)
            time.sleep(reconnect_time)

        if self._player_games < settings.MAX_GAMES:
            logging.info("[game_over] AiCEE will join new game. (%s/%s).", self._player_games, settings.MAX_GAMES)
            utils.restart_program()
        else:
            logging.info("[game_over] already played %s games. won't join new game", self._player_games)

    def _save_summarize(self):
        summarize = dict()
        summarize['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        summarize['table_number'] = self.number
        summarize['chips'] = self._chips
        summarize['round_count'] = self.round_count

        utils.generate_summarize_log(summarize)

    def other_players_allin(self):
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

    def is_big_blind_player(self, md5):
        return self.big_blind.playerName == md5

    def is_small_blind_player(self, md5):
        return self.small_blind.playerName == md5

    def number_player(self):
        num = 0
        for player in self.players:
            if player.is_survive:
                num += 1
        return num


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

