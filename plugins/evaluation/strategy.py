import logging
import player


class StrategyEvaluator(object):
    def __init__(self):
        pass

    @staticmethod
    def evaluate(table, win_prob, chip):
        is_all_in = False
        thresholds = [0.95, 0.8, 0.7, 0.1] # allin, raise, call, check, fold

        for player in table.players:
            if player.allin and player.is_survive:
                logging.info("player name: %s, is_all_in: %s", player.md5, player.allin)
                is_all_in = True

        # to avoid first player is trying to all-in at pre-flop
        if is_all_in and table.stages.index(table.round_name) == 0:
            if win_prob <= 0.9:
                thresholds = [0.99, 0.99, 0.99, 0.99]

        # flop
        if is_all_in and table.stages.index(table.round_name) == 1:
	        if win_prob >= 0.7:
		        thresholds = [0.95, 0.9, 0.8, 0.2]

		# turn
        if is_all_in and table.stages.index(table.round_name) == 2:
            if win_prob >= 0.7:
                thresholds = [0.95, 0.9, 0.6, 0.2]

        if is_all_in and table.stages.index(table.round_name) == 3:
            if win_prob >= 0.9:
                thresholds = [0.9, 0.8, 0.7, 0.5]

        return thresholds

    def _evaluate_winners_rank(self, table):
        sorted(self.players, key=attrgetter('chips'))





