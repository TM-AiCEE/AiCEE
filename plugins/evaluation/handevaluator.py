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

        n = self._simulation_number
        evaluator = Evaluator()

        # current hand win_prob
        rank = evaluator.evaluate(hands, board_cards)
        rank_class = evaluator.get_rank_class(rank)
        class_string = evaluator.class_to_string(rank_class)
        win_prob = 1.0 - evaluator.get_five_card_rank_percentage(rank)

        # simulation hand+boards+draw(2) win_prob
        total_win_prob = 0
        for i in range(n):
            to_draw_number = 5 - len(board_cards)
            board_cards = self._calculate_cards_to_draw(board_cards, to_draw_number)
            rank = evaluator.evaluate(board_cards, hands)
            win_prob = 1.0 - evaluator.get_five_card_rank_percentage(rank)
            total_win_prob += win_prob

        sim_win_prob = total_win_prob / n

        return win_prob, sim_win_prob, class_string

    def evaluate_postflop_win_prob(self, cards, boards):
        hands = self._converter_to_card(cards)
        board_cards = self._converter_to_card(boards)

        win_prob, sim_win_prob, class_string = self._calculate_win_prob(hands, board_cards)

        logging.info("[evaluate_postflop_win_prob] hand: %s, win_prob: %s, hand= {%s}, sim win_prob: %s",
                     Card.print_pretty_cards(hands + board_cards), win_prob, class_string, sim_win_prob)

        if win_prob > sim_win_prob:
            return win_prob

        return sim_win_prob

    def evaluate_preflop_win_prob(self, cards, num_player):
        cards = self._converter_to_card(cards)
        cards = sorted(cards, reverse=True)

        key = ''.join([Card.int_to_str(card)[0] for card in cards])

        if Card.get_rank_int(cards[0]) != Card.get_rank_int(cards[1]):
            if Card.get_suit_int(cards[0]) == Card.get_suit_int(cards[1]):
                key = key + "s"
            else:
                key = key + "o"

        odds = 0
        for item_key, item_value in self._lookup.items():
            if item_key == key and num_player != 0:
                logging.info("[evaluate_preflop_win_prob] %s, %s, %s, %s",
                             Card.print_pretty_cards(cards),
                             item_key, str(num_player-1), self._lookup[key][0].get(str(num_player-1)))
                odds = float(self._lookup[key][0].get(str(num_player-1)))

                # pair
                if Card.get_rank_int(cards[0]) == Card.get_rank_int(cards[1]):
                    odds *= 2.0
        return odds

