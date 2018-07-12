
class ChipEvaluator(object):
    def __init__(self, table):
        self.table = table

    @staticmethod
    def evaluate(self, hand_rank, is_bet_event=False):
        if is_bet_event and hand_rank > 0.5:
            return 100
        if is_bet_event and hand_rank > 0.3:
            return 20
        if is_bet_event and hand_rank < 0.3:
            return 10
        else:
            if hand_rank > 0.3:
                return 20
            elif hand_rank > 0.5:
                return 30
            else:
                return 10
        return 10

