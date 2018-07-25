# -*- coding:utf-8 -*-
import json
import logging
import hashlib

from enum import Enum
from plugins.evaluation.handevaluator import HandEvaluator
from plugins.evaluation.chipevaluator import ChipEvaluator

logger = logging.getLogger(__name__)


class Player(object):

    ACTIONS_CLASS_TO_STRING = {
        0: "BET",
        1: "CALL",
        2: "RAISE",
        3: "CHECK",
        4: "FOLD",
        5: "ALLIN"
    }

    class Actions(Enum):
        BET = 0
        CALL = 1
        RAISE = 2
        CHECK = 3
        FOLD = 4
        ALLIN = 5

    class PlayerInfo(object):
        def __init__(self, md5, chips, folded, allin, is_survive, reload_count, round_bet, bet, cards=[],
                     is_online=False):
            self.md5 = md5
            self.chips = chips
            self.folded = folded
            self.allin = allin
            self.is_survive = is_survive
            self.reload_count = reload_count
            self.round_bet = round_bet
            self.bet = bet
            self.cards = cards
            self.win_money = 0

    def __init__(self, md5):
        self.md5 = md5
        self.chips = 0
        self.folded = False
        self.allin = False
        self.is_survive = False
        self.reload_count = 0
        self.round_bet = 0
        self.bet = 0
        self.cards = []
        self.is_online = False
        self.is_human = False

    def update(self, player_info):
        self.md5 = player_info.md5
        self.chips = player_info.chips
        self.folded = player_info.folded
        self.allin = player_info.allin
        self.is_survive = player_info.is_survive
        self.reload_count = player_info.reload_count
        self.round_bet = player_info.round_bet
        self.cards = player_info.cards

        # end of round
        if hasattr(player_info, 'hand'):
            self.hand = player_info.hand

        # end of round
        if hasattr(player_info, 'win_money'):
            self.win_money = player_info.win_money


class Bot(Player):
    def __init__(self, client, name):
        self.client = client
        self.minibet = None
        self.name = name
        md5 = hashlib.md5(name.encode('utf-8')).hexdigest()
        super(Bot, self).__init__(md5)

    def update_self(self, info):
        self.md5 = info.playerName
        self.chips = info.chips
        self.folded = info.folded
        self.allin = info.allIn
        self.cards = info.cards
        self.is_survive = info.isSurvive
        self.round_bet = info.roundBet
        self.reload_count = info.reloadCount
        self.bet = info.bet
        self.is_online = info.isOnline
        self.is_human = info.isHuman
        # __action, request any action
        self.minibet = info.minBet

    def join(self):
        logging.info("player name: %s(%s) is going to join.", self.name, self.md5)
        self.client.send(json.dumps({
            "eventName": "__join",
            "data": {
                "playerName": self.name
            }
        }))

    def _take_action(self, event_name, action, amount=0):

        # If the action is 'bet', the message must include an 'amount'
        if event_name == "__bet":
            self.client.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": "bet",
                    "amount": amount
                }
            }))
        else:
            # "call", "check", "fold", "allin", "raise"
            if Player.Actions.CALL == action:
                self.client.send(json.dumps({
                    "eventName": "__action",
                    "data": {
                        "action": "call"
                    }
                }))
            elif Player.Actions.FOLD == action:
                self.client.send(json.dumps({
                    "eventName": "__action",
                    "data": {
                       "action": "fold",
                   }
                }))
            elif Player.Actions.RAISE == action:
                self.client.send(json.dumps({
                    "eventName": "__action",
                    "data": {
                        "action": "raise",
                    }
                }))
            elif Player.Actions.ALLIN == action:
                self.client.send(json.dumps({
                    "eventName": "__action",
                    "data": {
                        "action": "allin",
                    }
                }))
            elif Player.Actions.CHECK == action:
                self.client.send(json.dumps({
                    "eventName": "__action",
                    "data": {
                        "action": "check",
                    }
                }))

    def _decide_action(self, win_prob, thresholds):

        if win_prob >= thresholds["allin"]:
            return Player.Actions.ALLIN
        elif win_prob >= thresholds["raise"]:
            return Player.Actions.RAISE
        elif win_prob >= thresholds["call"]:
            return Player.Actions.CALL
        elif win_prob >= thresholds["check"]:
            return Player.Actions.CHECK
        else:
            return Player.Actions.FOLD

    def do_actions(self, table, is_bet_event=False):

        # pre-flop
        if table.round_name == "Deal":
            win_prob = HandEvaluator().evaluate_preflop_win_prob(self.cards, len(table.players))
            thresholds = {"check": 0.15, "call": 0.15, "allin": 0.98, "bet": 0.6, "raise": 0.8, "chipsguard": 0.7}

        # flop, three cards on board
        elif table.round_name == "Flop":

            thresholds = {"check": 0.15, "call": 0.15, "allin": 0.98, "bet": 0.4, "raise": 0.8, "chipsguard": 0.7}

            win_prob = HandEvaluator().evaluate_postflop_win_prob(self.cards, table.board)

            act = Player.Actions.CHECK
            chips = 10
            if win_prob < thresholds["bet"]:
                act = Player.Actions.BET
                self._take_action("__bet", act, chips)
            else:
                self._take_action("__action", act)

            logging.info("[do_actions] AiCEE's actions is (%s), amount (%d)",
                         super(Bot, self).ACTIONS_CLASS_TO_STRING[act.value], chips)
            return

        elif table.round_name == "Turn":
            win_prob = HandEvaluator().evaluate_postflop_win_prob(self.cards, table.board)
            thresholds = {"check": 0.3, "call": 0.3, "allin": 0.98, "bet": 0.6, "raise": 0.8, "chipsguard": 0.7}
            
        # turn, river
        else:
            win_prob = HandEvaluator().evaluate_postflop_win_prob(self.cards, table.board)
            thresholds = {"check": 0.3, "call": 0.3, "allin": 0.98, "bet": 0.6, "raise": 0.8, "chipsguard": 0.7}

        # action decision
        chips = 0
        if is_bet_event:
            if win_prob > thresholds["bet"]:
                if chips <= self.chips * thresholds["chipsguard"]:
                    self._take_action("__bet", Player.Actions.BET, chips)
                else:
                    self._take_action("__action", Player.Actions.CHECK)
        else:
            act = self._decide_action(win_prob, thresholds)

            # some player all-in rules
            if table.has_allin():
                logging.info("[do_actions] use all-in rules")
                if win_prob >= 0.90:
                    act = Player.Actions.ALLIN

            # chips rate rules
            chips_rate = self.chips / table.total_chips()
            if chips_rate >= 0.5 and win_prob <= 0.90:
                logging.info("[do_actions] use chips protected rules")
                action = Player.Actions.FOLD

            self._take_action("__action", act)

            logging.info("[do_actions] aicee's actions is (%s), amount (%d)",
                         super(Bot, self).ACTIONS_CLASS_TO_STRING[act.value], chips)
