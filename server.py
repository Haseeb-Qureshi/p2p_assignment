import time
from flask import Flask, request
from threading import Timer, Lock
from primes import find_next_mersenne_prime
import sys
import requests
import random
import ipdb # TODO:REMOVE

if len(sys.argv) < 2: raise Exception("Must pass in port number")
MY_PORT = int(sys.argv[1])
if MY_PORT < 1024: raise Exception("Port number must be >= 1024")

# Connected peers (key: port number, value: when we last heard from them)
PEERS = {}

# If passed in another peer's port, initialize that peer with no message history
if len(sys.argv) >= 3: PEERS[int(sys.argv[2])] = 0

# Choose a human-readable name
names = open("names.txt", "r").read().split("\n")
MY_NAME = random.choice(names)

# Settings
RANDOM_DISCONNECTS = False
ASLEEP = False
INFECTION_FACTOR = 2

# Message types
PING = "PING"
PONG = "PONG"
PRIME = "PRIME"
MESSAGE_TYPES = set([PING, PONG, PRIME])

# Monotonically increasing message counter
MSG_ID = 0

# List of all messages we've received from peers
MESSAGE_HISTORY = []

# Biggest prime we've seen so far (starts at 2)
BIGGEST_PRIME = 2

# Sender of the current biggest prime (starts as self)
BIGGEST_PRIME_SENDER = MY_PORT

# Lock to avoid race conditions
LOCK = Lock()

app = Flask(__name__)

# TODO: Put all locks into a central clearinghouse of state changes

def send_message_to(peer, message):
	'''
	Send point-to-point message to a specific peer. Node-specific metadata is
	automatically added. Only one message is sent out at a time to avoid
	race conditions.
	'''
	global MSG_ID
	if type(peer) is not int:
		raise TypeError("Tried to send a message to non-integer: %d" % peer)
	if not "ttl" in message:
		raise Exception("Must have a TTL")
	if not "msg_type" in message or message["msg_type"] not in MESSAGE_TYPES:
		raise Exception("Must have a valid msg_type")

	with LOCK:
		message.update({
			"msg_source": MY_PORT,
			"msg_id": MSG_ID,
			"current_hops": 0,
		})
		try:
			req = requests.post(
				"http://localhost:%d/receive" % peer,
				json=message
			)
		except requests.exceptions.RequestException as err:
			print(err)
			MESSAGE_HISTORY.append(str(err))
		MSG_ID += 1

def send_pings_to_everyone():
	ping = {
		"msg_type": PING,
		"ttl":  0,
		"data": None,
	}

	for peer in PEERS.keys():
		send_message_to(peer=peer, message=ping)

def gossip_prime_number(prime):
	prime_message = {
		"msg_type": PRIME,
		"ttl": 2,
		"data": prime,
	}

	num_peers_to_gossip_to = min(INFECTION_FACTOR, len(PEERS))
	for peer in random.sample(PEERS.keys(), num_peers_to_gossip_to):
		send_message_to(peer=peer, message=prime_message)

def log_message(message):
	MESSAGE_HISTORY.append(message)

def log_message_from(peer, message):
	PEERS[peer] = time.monotonic() # Update latest timestamp
	log_message(message)

def evict_peers():
	'''
	Evicts any peers who we haven't heard from in the last 10 seconds.
	'''
	current_time = time.monotonic()
	peers_to_remove = [p for p in PEERS.keys() if current_time - PEERS[p] > 10]

	with LOCK:
		for peer in peers_to_remove:
			PEERS.pop(peer)

def generate_next_mersenne_prime():
	'''
	Generates the next Mersenne prime and gossips it to our peers.
	Runs once every 10 seconds.
	'''
	global BIGGEST_PRIME, BIGGEST_PRIME_SENDER
	new_prime = find_next_mersenne_prime(BIGGEST_PRIME)
	BIGGEST_PRIME = new_prime
	BIGGEST_PRIME_SENDER = MY_PORT
	gossip_prime_number(new_prime)

@app.route("/message_log")
def message_log():
	'''
	Reads out the last 5 messages received by this node.
	'''
	return MESSAGE_HISTORY[:5]

@app.route("/")
def state():
	'''
	Reads out the current state of this node.
	'''
	return {
		"name": MY_NAME,
		"port": MY_PORT,
		"peers": PEERS,
		"biggest_prime": BIGGEST_PRIME,
		"biggest_prime_sender": BIGGEST_PRIME_SENDER,
	}

@app.route("/receive", methods=["POST"])
def receive():
	# Static code
	req_data = request.get_json()
	log_message(req_data)

	msg_type = req_data["msg_type"]
	msg_id = req_data["msg_id"]
	msg_source = req_data["msg_source"]
	current_hops = int(req_data["current_hops"])
	ttl = int(req_data["ttl"])
	data = req_data["data"]

	from respond_to_message import respond
	with LOCK:
		return respond(msg_type, msg_id, msg_source, ttl, current_hops, data)

@app.route("/enable_disconnects", methods=["POST"])
def enable_disconnects():
	global RANDOM_DISCONNECTS
	RANDOM_DISCONNECTS = True
	return "OK"

@app.route("/disable_disconnects", methods=["POST"])
def disable_disconnects():
	global RANDOM_DISCONNECTS
	RANDOM_DISCONNECTS = False
	return "OK"

class Interval(Timer):
	def run(self):
		while not self.finished.wait(self.interval): self.function()

if __name__ == "__main__":
	print("My name is %s" % MY_NAME)

	# Send ping every 5 seconds
	ping_timer = Interval(5.0, send_pings_to_everyone)
	ping_timer.start()

	# Evict a peer if they haven't responded to a ping or sent a ping themselves
	eviction_timer = Interval(1.0, evict_peers)
	eviction_timer.start()

	# Send a new Mersenne prime every 10 seconds
	prime_timer = Interval(10.0, generate_next_mersenne_prime)
	prime_timer.start()

	app.run(host="0.0.0.0", port=MY_PORT)
