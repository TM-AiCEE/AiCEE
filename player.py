# -*- coding:utf-8 -*-
import json
import logging
import hashlib

from enum import Enum
from plugins.evaluation.model import HandEvaluator
from plugins.evaluation.chipevaluator import ChipEvaluator
from plugins.evaluation.strategy import StrategyEvaluator

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
        self.minibet = info.minBet

    def join(self):
        logging.info("player name: %s(MD5(%s)) is going to join.", self.name, self.md5)
        self.client.send(json.dumps({
            "eventName": "__join",
            "data": {
                "playerName": self.name
            }
        }))

    def _take_action(self, table, event_name, action, amount=0):

        logging.info("player's actions is (%s), amount (%d)",
                     super(Bot, self).ACTIONS_CLASS_TO_STRING[action.value], amount)

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

    def do_actions(self, table, is_bet_event=False):

        # pre-flop strength
        if table.stages.index(table.round_name) == table.STAGE.Preflop:
            win_prob = HandEvaluator().evaluate_preflop_win_prob(self.cards, table.get_survive_player_num())

        # flop, turn, river strength (using MonteCarlo)
        else:
            win_prob = HandEvaluator().evaluate_postflop_win_prob(self.cards, table.board, len(table.players))

        # chip evaluator based on win_prob
        chip = ChipEvaluator(table).evaluate(win_prob, is_bet_event)

        # rule-based strategy
        threshold = StrategyEvaluator().evaluate(table, win_prob, chip)

        logger.info("after evaluator, the win_prob is %f", win_prob)
        logger.info("allin: %f, raise: %f, call: %f, check: %f",
                    threshold[Player.Actions.ALLIN.value], threshold[Player.Actions.RAISE.value],
                    threshold[Player.Actions.CALL.value], threshold[Player.Actions.CHECK.value])

        if is_bet_event:
            self._take_action(table, "__bet", Player.Actions.BET, chip)
        else:
            if win_prob >= threshold[Player.Actions.ALLIN.value]:
                self._take_action(table, "__action", Player.Actions.ALLIN)
            elif win_prob >= threshold[Player.Actions.RAISE.value]:
                self._take_action(table, "__action", Player.Actions.RAISE)
            elif win_prob >= threshold[Player.Actions.CALL.value]:
                self._take_action(table, "__action", Player.Actions.CALL)
            elif win_prob >= threshold[Player.Actions.CHECK.value]:
                self._take_action(table, "__action", Player.Actions.CHECK)
            else:
                self._take_action(table, "__action", Player.Actions.FOLD)
