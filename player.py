# -*- coding:utf-8 -*-
import json
import logging
import hashlib
import settings

from enum import Enum
from handevaluator import HandEvaluator


logger = logging.getLogger(__name__)


class PlayerAction(object):
    # action: bet, call, raise, check, fold, allin
    def __init__(self, act, name, amount, chips):
        self.act = act
        self.md5 = name
        self.amount = amount
        self.chips = chips


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
        def __init__(self, md5, chips, folded, allin, is_survive, reload_count, round_bet, bet, cards=[]):
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
        self.hand = None
        self.win_money = 0

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
        logging.info("[join] player name: %s(%s) is going to join.", self.name, self.md5)
        self.client.send(json.dumps({
            "eventName": "__join",
            "data": {
                "playerName": self.name
            }
        }))

    def _take_action(self, action, t, amount=0):

        if settings.ALWAYS_FOLD:
            action = Player.Actions.FOLD

        if action == Player.Actions.BET:
            logging.debug("[do_actions] AiCEE's actions is (%s), amount (%d)",
                         super(Bot, self).ACTIONS_CLASS_TO_STRING[action.value], amount)
        else:
            if action == Player.Actions.CALL:
                if len(t.player_actions) > 0:
                    last_action = t.player_actions[0]
                    logging.debug("[do_actions] AiCEE's actions is (%s), amount (%d)",
                                 super(Bot, self).ACTIONS_CLASS_TO_STRING[action.value], last_action.amount)
            else:
                logging.debug("[do_actions] AiCEE's actions is (%s), amount (0)",
                             super(Bot, self).ACTIONS_CLASS_TO_STRING[action.value])

        # If the action is 'bet', the message must include an 'amount'
        if Player.Actions.BET == action:
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

    @staticmethod
    def _decide_action(win_prob, thresholds):

        logger.debug("[do_actions] current thresholds: %s", thresholds)

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
        t = table

        # pre-flop
        if table.round_name == "Deal":
            win_prob = HandEvaluator().evaluate_preflop_win_prob(self.cards, t.number_player())
            thresholds = {"check": 0.15, "call": 0.20, "bet": 0.6, "raise": 0.8, "allin": 0.98, "chipsguard": 0.2}

            # decide by win_prob
            act = self._decide_action(win_prob, thresholds)

            # avoid other players all-in rule
            act = self.decide_action_by_last_action(t, act, win_prob, thresholds)

            # apply Big-blind rule if you're in BB
            act = self.decide_action_when_bigblind_player(t, act, win_prob)

            if act == Player.Actions.BET:
                chips = self.decide_action_by_chips_rate(win_prob, thresholds)
                self._take_action(act, t, chips)
            else:
                self._take_action(act, t)

        # flop, turn, river
        else:
            win_prob = HandEvaluator().evaluate_postflop_win_prob(self.cards, table.board)
            thresholds = {"check": 0.20, "call": 0.25, "bet": 0.4, "raise": 0.8, "allin": 0.98, "chipsguard": 0.4}

            # decide by win_prob
            act = self._decide_action(win_prob, thresholds)

            # avoid other players all-in rule
            act = self.decide_action_by_last_action(t, act, win_prob, thresholds)

            # apply Big-blind rule if you're in BB
            act = self.decide_action_when_bigblind_player(t, act, win_prob)

            # handle bet event
            if is_bet_event:
                act = Player.Actions.BET if win_prob < thresholds["bet"] else Player.Actions.CHECK
                chips = self.decide_action_by_chips_rate(win_prob, thresholds)
                self._take_action(act, chips)
                logger.debug("[do_actions] handle bet event, chips: %s", chips)
            else:
                self._take_action(act, t)

    def decide_action_by_last_action(self, t, act, win_prob, thresholds):

        # do nothing, return default act
        if len(t.player_actions) <= 0:
            logger.debug("[do_actions] no actions data.")
            act = Player.Actions.FOLD
            return act

        # avoid other players all-in rule
        last_action = t.player_actions.pop(0)
        if t.other_players_allin() and last_action.amount > self.chips * thresholds["chipsguard"]:
            if win_prob <= 0.7:
                act = Player.Actions.FOLD
                logger.debug("[do_actions] use avoid other players all-in rule.")

        # avoid other players all-in rule
        if last_action.md5 is not self.md5:
            player = t.find_player(last_action.md5)
            if last_action.chips >= 0 and last_action.amount > settings.MAX_AMOUNT_CHIPS_ROUND * 2:
                act = Player.Actions.FOLD
                logger.debug("[do_actions] use avoid other player bet big amount. (%s) (%s)",
                             last_action.amount, settings.MAX_AMOUNT_CHIPS_ROUND * 2)

            if player and not player.allin:
                other_player_chips_risk = 0.6 if last_action.chips == 0 else last_action.amount / last_action.chips
                if win_prob < 0.6:
                    if other_player_chips_risk >= 0.6:
                        act = Player.Actions.FOLD
                        logger.debug("[do_actions] use avoid other player bet big amount. %s, %s, risk: %s",
                                     last_action.amount, last_action.chips, other_player_chips_risk)

            if last_action.amount >= self.chips * 0.7:
                if win_prob < 0.7:
                    act = Player.Actions.FOLD
                    logger.debug("[do_actions] use avoid other players bet big amount. %s, my chips: %s.",
                                 last_action.amount, self.chips)

        # protected by rank
        chips_risk = self.chips / t.total_chips()
        if chips_risk >= 0.3 and win_prob < 0.4 and t.round_name == 'Deal':
            act = Player.Actions.FOLD
            logger.debug("[do_actions] protected chip by rank.")
        if chips_risk >= 0.3 and win_prob < 0.7 and t.round_name != 'Deal':
            act = Player.Actions.FOLD
            logger.debug("[do_actions] protected chip by rank.")

        return act

    def decide_action_when_bigblind_player(self, t, act, win_prob):
        if t.is_big_blind_player(self.md5):
            logger.debug("[do_actions] AiCEE (%s) is big-blind player. amount: %s",
                        t.big_blind.playerName[:5], t.big_blind.amount)
            if t.big_blind.amount >= settings.MAX_AMOUNT_CHIPS_ROUND:
                if win_prob < 0.6:
                    act = Player.Actions.FOLD
                    logger.debug("[do_actions] use Big-blind rule.")
        return act

    def decide_action_by_chips_rate(self, win_prob, thresholds):
        chips = self.chips * win_prob * settings.default_chips_rate

        if chips >= self.chips * thresholds["chipsguard"]:
            chips = self.chips * thresholds["chipsguard"]
            logger.debug("[do_actions] use chips guard rule.")

        if chips >= settings.MAX_AMOUNT_CHIPS_ROUND:
            chips = settings.MAX_AMOUNT_CHIPS_ROUND
            logger.debug("[do_actions] use max amount chips in round rule.")

        return chips
