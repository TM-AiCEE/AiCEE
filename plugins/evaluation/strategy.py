import logging


class StrategyEvaluator(object):
    def __init__(self):
        pass

    @staticmethod
    def evaluate(table, win_prob, chip):
        is_all_in = False
        # bet, call, raise, check, fold, allin
        thresholds_actions = [1.0, 0.7, 0.8, 0.1, 0, 0.95]

        for player in table.players:
            if player.allin and player.is_survive:
                logging.info("player name: %s, is_all_in: %s", player.md5, player.allin)
                is_all_in = True

        # to avoid some players want to all-in at "pre-flop"
        if is_all_in and table.stages.index(table.round_name) == table.STAGE.Preflop:
            if win_prob <= 0.9:
                thresholds_actions = [0.99, 0.99, 0.99, 0.99, 0.99, 0.99]

        if is_all_in and table.stages.index(table.round_name) == table.STAGE.Flop:
            if win_prob >= 0.7:
                thresholds_actions = [1.0, 0.3, 0.2, 0.5, 0.1, 0.6]

        if is_all_in and table.stages.index(table.round_name) == table.STAGE.Turn:
            if win_prob >= 0.7:
                thresholds_actions = [0.95, 0.9, 0.6, 0.7, 0.2, 0.8]

        if is_all_in and table.stages.index(table.round_name) == table.STAGE.River:
            if win_prob >= 0.9:
                thresholds_actions = [0.95, 0.9, 0.6, 0.7, 0.2, 0.8]

        return thresholds_actions






