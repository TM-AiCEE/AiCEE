import logging
import settings
import utils

from run import receive_from
from player import Player
from table import TableManager

logger = logging.getLogger(__name__)


@receive_from("__new_peer")
def new_peer(message):
    d = message.data
    t = TableManager().current()

    for md5 in d:
        if t:
            player = t.find_player(md5)
            if player is None:
                t.add_player_by_md5(md5.playerName)


@receive_from("__new_peer_2")
def new_peer_2(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.number = d.tableNumber
        t.status = d.tableStatus
        logger.info("[__new_peer_2] table number is: %s", t.number)
        if settings.TRAINING_MODE:
            logger.info("[__new_peer_2] http://poker-training.vtr.trendnet.org:3001/game.html?table=%s", t.number)
        utils.generate_logs(t.number)

    for pjson in d.players:
        player = t.find_player(pjson.playerName)
        if player:
            player.is_online = pjson.isOnline
        else:
            player = Player(pjson.playerName)
            player.is_online = pjson.isOnline
            logger.info("[__new_peer_2] player name is: %s, is_online: %s", player.md5[:5], player.is_online)


@receive_from("__new_round")
def start_of_new_round(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.new_round()
        t.update_table(d.table)
        t.update_players(d.players)


@receive_from("__deal")
def deal(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_table(d.table)
        t.update_players(d.players)


@receive_from("__action")
def handle_action_requests(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_table(d.game)
        t.update_players(d.game.players)

        player = t.bot()
        if player:
            player.update_self(d.self)
            player.do_actions(t)


@receive_from("__bet")
def request_bet(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_table(d.game)
        t.update_players(d.game.players)

        player = t.bot()
        if player:
            player.update_self(d.self)
            player.do_actions(t, True)


@receive_from("__show_action")
def update_board_info(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_table(d.table)
        t.update_players(d.players)
        t.update_action(d.action)
        t.show_action()


@receive_from("__round_end")
def end_round(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_table(d.table)
        t.update_players(d.players)
        t.end_round()


@receive_from("__game_over")
def game_over(message):
    d = message.data
    t = TableManager().current()

    if t:
        t.update_players(d.players)
        t.update_table(d.table)
        t.update_winners_info(d.winners)
        t.game_over()



