import logging
import player


class StrategyEvaluator(object):
    def __init__(self):
        pass

    @staticmethod
    def evaluate(table, win_prob, chip):
        is_all_in = False
        thresholds = [0.95, 0.7, 0.4, 0.2] # allin, raise, call, check, fold

        for player in table.players:
            if player.allin:
                logging.info("player name: %s, is_all_in: %s", player.md5, player.allin)
                is_all_in = True

        # to avoid first player is trying to all-in
        if is_all_in:
            if win_prob <= 0.8:
                thresholds = [0.99, 0.99, 0.99, 0.99]

        # if table.stages.index(table.round_name) == 0:
        #    thresholds = [0.99, 0.5, 0.2, 0.1]

        return thresholds


