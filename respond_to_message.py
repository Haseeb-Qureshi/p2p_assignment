from server import PEERS, send_message_to, log_message
from server import PING, PONG, PRIME

def respond(msg_type, msg_id, msg_source, ttl, current_hops, data):
    if msg_type == PING: # received a ping
        pass
    elif msg_type == PONG: # received a pong
        pass
    elif msg_type == PRIME: # got a prime number from someone
        pass

def reply_with_pong(peer):
	pong_message = {
		"msg_type": PONG,
		"ttl": 0,
		"data": None,
	}

	send_message_to(message=pong_message, peer=peer)
