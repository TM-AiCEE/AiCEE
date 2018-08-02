import logging
import json

from random import sample
from plugins.treys import Card
from plugins.treys import Evaluator
from plugins.treys import Deck


class PseudoDesk:
    def __init__(self, deck):
        self._cards = list(deck)

    def draw(self, n=2):
        return sample(self._cards, n)


class HandEvaluator(object):

    def __init__(self):
        self._simulation_number = 10000
        self._win_rate = 0
        self._deck = Deck()
        self._lookup = json.load(open("data/preflop_odds.json"))

    @staticmethod
    def _converter_to_card(cards_from_s):
        cards = list()

        for card in cards_from_s:
            c = card.lower().capitalize()
            cards.append(Card.new(c))

        return cards

    @staticmethod
    def _calculate_cards_to_draw(boards, cards_to_draw):
        sample_board = boards

        board = self._desk.draw(cards_to_draw)
        if type(board) is int:
            sample_board.append(board)
        else:
            for card in board:
                sample_board.append(card)

        # for card in sample_board:
        #    if card in self._deck.cards:
        #        self._deck.remove(card)
        #    logging.info('Unused cards: {0}'.format(len(self._deck.cards)))

        return sample_board

    def print_pretty_cards(self, cards):
        return Card.print_pretty_cards(self._converter_to_card(cards))

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
        pd = PseudoDesk(self._deck.cards)
        for i in range(n):
            hand = pd.draw(2)
            sim_rank = evaluator.evaluate(hand, boards)
            if sim_rank is None:
                continue
            win_prob = 1.0 - evaluator.get_five_card_rank_percentage(sim_rank)
            total_win_prob += win_prob
        sim_win_prob = total_win_prob / n

        return win_prob, sim_win_prob, class_string

    def evaluate_postflop_win_prob(self, cards, boards):
        hands = self._converter_to_card(cards)
        board_cards = self._converter_to_card(boards)

        win_prob, sim_win_prob, class_string = self._calculate_win_prob(hands, board_cards)

        if win_prob > sim_win_prob:
            logging.info("[postflop_win_prob] hand: %s, win_prob: %s, hand= {%s}, "
                         "sim win_prob: %s, use [%s].",
                         Card.print_pretty_cards(hands + board_cards),
                         "{:.1%}".format(win_prob),
                         class_string,
                         "{:.1%}".format(sim_win_prob),
                         "{:.1%}".format(win_prob))
            return win_prob
        else:
            logging.info("[postflop_win_prob] hand: %s, win_prob: %s, hand= {%s}, "
                         "sim win_prob: %s, use [%s].",
                         Card.print_pretty_cards(hands + board_cards),
                         "{:.1%}".format(win_prob),
                         class_string,
                         "{:.1%}".format(sim_win_prob),
                         "{:.1%}".format(sim_win_prob))

        return sim_win_prob

    # refer to pre-flop-odds
    # http://www.natesholdem.com/pre-flop-odds.php
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
            if item_key == key and num_player >= 2:
                logging.info("[preflop_win_prob] cards: %s (%s), number of player: %s, win_prob: %s",
                             Card.print_pretty_cards(cards),
                             item_key, str(num_player), self._lookup[key][0].get(str(num_player)))
                odds = float(self._lookup[key][0].get(str(num_player)))
        return odds


