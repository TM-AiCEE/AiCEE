import logging

from plugins.treys import Card
from plugins.treys import Evaluator
from plugins.treys import Deck


class HandEvaluator(object):

    def __init__(self):
        self.simulation_number = 5000
        self.win = 0

    @staticmethod
    def _converter_to_card(scards, sboards):
        hands, board_cards = [], []

        for card in scards:
            c = card.lower().capitalize()
            hands.append(Card.new(c))

        for card in sboards:
            c = card.lower().capitalize()
            board_cards.append(Card.new(c))

        return hands, board_cards

    @staticmethod
    def _calculate_cards_to_draw(boards, cards_to_draw):
        sample_board = boards

        board = Deck().draw(cards_to_draw)
        if type(board) is int:
            sample_board.append(board)
        else:
            for card in board:
                sample_board.append(card)

        return sample_board


    def calculate_win_prob(self, hands, boards):
        board_cards = boards

        logging.debug("board_cards is:")
        Card.print_pretty_cards(boards)

        evaluator = Evaluator()
        to_draw_number = 5 - len(board_cards)
        board_cards = self._calculate_cards_to_draw(board_cards, to_draw_number)
        rank = evaluator.evaluate(hands, board_cards)
        rank_class = evaluator.get_rank_class(rank)
        class_string = evaluator.class_to_string(rank_class)
        win_prob = 1.0 - evaluator.get_five_card_rank_percentage(rank)

        logging.debug("sample board cards is:")
        Card.print_pretty_cards(board_cards)
        logging.debug("hand cards is:")
        Card.print_pretty_cards(hands)
        logging.debug("hand = {}, percentage rank among all hands = {}".format(class_string, win_prob))

        return win_prob

    def evaluate_hand(self, cards, boards, num_player):
        hands, board_cards = self._converter_to_card(cards, boards)
        win_prob = self.calculate_win_prob(hands, board_cards)
        return win_prob

