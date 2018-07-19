
class ChipEvaluator(object):
    def __init__(self, table):
        self.table = table

    @staticmethod
    def evaluate(win_rate, is_bet_event=False, smallblind=10, bigblind=20):

        if is_bet_event and win_rate > 0.9:
            return bigblind
        if is_bet_event and win_rate > 0.5:
            return smallblind
        if is_bet_event and win_rate < 0.3:
            return smallblind
        else:
            if win_rate > 0.9:
                return bigblind
            elif win_rate > 0.3:
                return smallblind
            else:
                return smallblind
        return smallblind

