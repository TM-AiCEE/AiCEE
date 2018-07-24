
class ChipEvaluator(object):
    def __init__(self, table):
        self.table = table

    @staticmethod
    def evaluate(t, win_rate, is_bet_event=False, smallblind=10, bigblind=20):

        player = t.bot()
        my_chips = player.chips

        chips_amount = 0

        if is_bet_event and win_rate > 0.9:
            chips_amount = my_chips * 0.4
        if is_bet_event and win_rate > 0.5:
            chips_amount = my_chips * 0.2
        if is_bet_event and win_rate < 0.3:
            chips_amount = my_chips * 0.01
        else:
            if win_rate > 0.9:
                chips_amount = my_chips * 0.4
            elif win_rate > 0.3:
                chips_amount = my_chips * 0.2
            else:
                chips_amount = my_chips * 0.1
        return chips_amount

