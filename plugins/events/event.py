import logging

from run import receive_from
from player import Player, Bot
from table import TableManager

logger = logging.getLogger(__name__)
table_mgr = TableManager()


@receive_from("__new_peer")
def new_peer(message):
    d = message.data
    t = table_mgr.current()

    for md5 in d:
        if t:
            player = t.find_player_by_md5(md5)
            if player is None:
                t.add_player_by_md5(md5)


@receive_from("__new_peer_2")
def new_peer_2(message):
    d = message.data
    t = table_mgr.current()

    if t:
        t.number = d.tableNumber
        t.status = d.tableStatus
        logger.info("the table number is updated to %s", t.number)

    for pjson in d.players:
        player = t.find_player_by_md5(pjson.playerName)
        if player:
            player.is_online = pjson.isOnline
            logging.info("player (MD5(%s)), online status is: (%s).", player.md5, player.is_online)
        else:
            player = Player(pjson.playerName)
            player.is_online = pjson.isOnline
            t.add_player(player)


@receive_from("__new_round")
def start_of_new_round(message):
    d = message.data
    t = table_mgr.current()
    if t:
        t.update_table(d.table)
        t.update_players(d.players)


@receive_from("__deal")
def deal(message):
    d = message.data
    t = table_mgr.current()
    if t:
        t.update_table(d.table)
        t.update_players(d.players)


@receive_from("__action")
def handle_action_requests(message):
    d = message.data
    t = table_mgr.current()

    if t and t.number == int(d.tableNumber):
        t.update_table(d.game)
        t.update_players(d.game.players)

        player = t.find_player_by_md5(d.self.playerName)
        if player is not None and type(player) is Bot:
            player.update_self(d.self)
            player.do_actions(t)


@receive_from("__bet")
def request_bet(message):
    d = message.data
    t = table_mgr.current()
    is_bet_event = True
    if t:
        t.update_table(d.game)
        t.update_players(d.game.players)

        player = t.find_player_by_md5(d.self.playerName)
        if player is not None and type(player) is Bot:
            player.update_self(d.self)
            player.do_actions(t, is_bet_event)


@receive_from("__show_action")
def update_board_info(message):
    d = message.data
    t = table_mgr.current()
    if t:
        t.update_table(d.table)
        t.update_players(d.players)
        t.update_action(d.action)


@receive_from("__round_end")
def end_round(message):
    d = message.data
    t = table_mgr.current()
    if t:
        t.update_table(d.table)
        t.update_players(d.players)


@receive_from("__game_over")
def game_over(message):
    d = message.data
    t = table_mgr.current()

    if t:
        t.update_players(d.players)
        t.update_table(d.table)
        t.update_winners(d.winners)
        t.end()



