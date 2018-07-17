import logging
import json

from plugins.treys import Card
from plugins.treys import Evaluator
from plugins.treys import Deck


class HandEvaluator(object):

    def __init__(self):
        self._simulation_number = 10000
        self._win_rate = 0
        self._lookup = json.load(open("data/preflop_odds.json"))

    @staticmethod
    def _converter_to_card(cards_from_s):
        cards = []

        for card in cards_from_s:
            c = card.lower().capitalize()
            cards.append(Card.new(c))

        return cards

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

    def _calculate_win_prob(self, hands, boards):
        board_cards = boards

        # PRE-FLOP, FLOP, TURN, RIVER, HAND OVER
        n = self._simulation_number
        total_win_prob = 0
        evaluator = Evaluator()

        Card.print_pretty_cards(hands + boards)

        if len(boards) >= 3:
            logging.debug("hands+boards:")
            Card.print_pretty_cards(hands+boards)
            rank = evaluator.evaluate(hands, board_cards)
            rank_class = evaluator.get_rank_class(rank)
            class_string = evaluator.class_to_string(rank_class)
            win_prob = 1.0 - evaluator.get_five_card_rank_percentage(rank)
            logging.debug("hand = {}, percentage rank among all hands = {}".format(class_string, win_prob))

        for i in range(n):
            to_draw_number = 5 - len(board_cards)
            board_cards = self._calculate_cards_to_draw(board_cards, to_draw_number)
            rank = evaluator.evaluate(board_cards, hands)
            win_prob = 1.0 - evaluator.get_five_card_rank_percentage(rank)
            total_win_prob += win_prob

        win_prob = total_win_prob / n
        logging.info("simulation win_prob: %s", win_prob)
        return win_prob

    def evaluate_postflop_win_prob(self, cards, boards, num_player):
        hands = self._converter_to_card(cards)
        board_cards = self._converter_to_card(boards)
        win_prob = self._calculate_win_prob(hands, board_cards)
        return win_prob

    def evaluate_preflop_win_prob(self, cards, num_player):
        cards = self._converter_to_card(cards)
        cards = sorted(cards, reverse=True)
        Card.print_pretty_cards(cards)

        key = ''.join([Card.int_to_str(card)[0] for card in cards])

        rank1 = Card.get_rank_int(cards[0])
        rank2 = Card.get_rank_int(cards[1])

        if Card.get_rank_int(cards[0]) != Card.get_rank_int(cards[1]):
            if Card.get_suit_int(cards[0]) == Card.get_suit_int(cards[1]):
                key = key + "s"
            else:
                key = key + "o"

        for item_key, item_value in self._lookup.items():
            if item_key == key:
                logging.info("%s, %s, %s", item_key, str(num_player-1), self._lookup[key][0].get(str(num_player-1)))
                if num_player - 1 < 0:
                    odds = float(self._lookup[key][0].get(str(1)))
                else:
                    odds = float(self._lookup[key][0].get(str(num_player-1)))
                if Card.get_rank_int(cards[0]) == Card.get_rank_int(cards[1]):
                    odds *= 2.0
        return odds


