# -*- coding:utf-8 -*-
import json
import logging

from enum import Enum
from plugins.evaluation.model import HandEvaluator
from plugins.evaluation.chipevaluator import ChipEvaluator

logger = logging.getLogger(__name__)


class Player:
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
    def __init__(self, client, name, md5, number = 0):
        self.client = client
        self.minibet = None
        self.number = number
        self.name = name
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

    def do_actions(self, table, is_bet_event=False):
        hand_rank = HandEvaluator().evaluate_hand(self.cards, table.board, len(table.players))
        amount = ChipEvaluator(table).evaluate(hand_rank, is_bet_event)

        if is_bet_event:
            self._take_action(table, "__bet", Player.Actions.BET, amount)
        else:
            if hand_rank > 0.99:
                self._take_action(table, "__action", Player.Actions.ALLIN)
            elif hand_rank > 0.7:
                self._take_action(table, "__action", Player.Actions.RAISE)
            elif hand_rank > 0.5:
                self._take_action(table, "__action", Player.Actions.CALL)
            elif hand_rank > 0.4:
                self._take_action(table, "__action", Player.Actions.CHECK)
            else:
                self._take_action(table, "__action", Player.Actions.FOLD)

    def _take_action(self, table, event_name, action, amount=0):
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
