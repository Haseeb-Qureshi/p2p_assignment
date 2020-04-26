from flask import Flask, request
from flask_cors import CORS
from threading import Timer
from waitress import serve
from backendy_stuff.primes import find_next_mersenne_prime
import os
import time
import functools
import traceback
import sys
import json
import requests
import random

if len(sys.argv) < 2: raise Exception("Must pass in port number")

MY_PORT = int(sys.argv[1])
if MY_PORT < 1024: raise Exception("Port number must be >= 1024")

# Randomly choose a human-readable name
names = open("names.txt", "r").read().split("\n")
MY_NAME = random.choice(names)

# Message types
PING = "PING"
PONG = "PONG"
PRIME = "PRIME"
MESSAGE_TYPES = set([PING, PONG, PRIME])

# Only do things if the node is awake
AWAKE = True

app = Flask(__name__)

# Enable cross-origin requests so localhost dashboard works
CORS(app)

# List of all messages we've seen before (so as not to re-transmit duplicates)
RECEIVED_MESSAGES = set()

# Message log
LOGS = []

# Global state object for reading and altering state: you should read and write to this
STATE = {
	"name": MY_NAME,
	"port": MY_PORT,
	"peers": {}, # (key: port number, value: timestamp when we last heard from them)
	"biggest_prime": 2, # Biggest Mersenne prime we've seen so far (starts at 2)
	"biggest_prime_sender": MY_PORT, # Sender of the current biggest prime (starts as self)
	"msg_id": 0, # Monotonically increasing message counter (we'll automatically increment this for you)
}

def respond(msg_type, msg_id, msg_forwarder, msg_originator, ttl, data):
	'''
	This is where the meat of the P2P protocol happens.
	Upon receiving a message from a peer, what does each node do?

	Args:
        msg_type (str): "PING", "PONG", or "PRIME"
        msg_id (int): The auto-incrementing message counter for each node
		msg_forwarder (int): The port of the immediate node that sent you this message
		msg_originator (int): The port of the node that created the original message (for a 0 TTL point-to-point message, this will be the same as the forwarder)
		ttl (int): Time-to-live—the number of hops remaining in the lifetime of this message until it should be dropped. A 0 TTL message should not be forwarded any further.
		data (int or None): The data in the message payload. For PINGs and PONGs, this will be None. For a PRIME message, the data field will contain the prime number.

    Returns:
        Nothing
	'''
	# TODO: Your code here!
	pass

def update_last_heard_from(peer):
	STATE["peers"][peer] = time.time()

def only_if_awake(f):
	'''
	Decorator that ensures a function only runs when the node is awake.
	If not, the node drops the request.
	'''
	@functools.wraps(f)
	def if_awake(*args, **kwargs):
		if AWAKE:
			return f(*args, **kwargs)
		else:
			return "Asleep"
	return if_awake

@only_if_awake
@app.route("/receive", methods=["POST"])
def receive():
	'''
	Entry-point when the node receives a message from another node.
	Parses the request and forwards it along to `respond`.
	You should not need to modify this function.
	'''
	req_data = request.get_json()
	log_message(message=req_data, received=True)

	msg_type = req_data["msg_type"]
	msg_id = int(req_data["msg_id"])
	msg_forwarder = int(req_data["msg_forwarder"])
	msg_originator = int(req_data["msg_originator"])
	ttl = int(req_data["ttl"])
	data = req_data["data"]

	try:
		respond(msg_type, msg_id, msg_forwarder, msg_originator, ttl, data)
	except Exception as e:
		log_error(e)

	return "OK"

@only_if_awake
def send_message_to(peer: int, message: dict, forwarded: bool):
	'''
	Send point-to-point message to a specific peer. Node-specific metadata is
	automatically added. You should not need to modify this function.
	'''
	if type(peer) is not int:
		raise TypeError("Tried to send a message to non-integer: %d" % peer)
	if not "ttl" in message:
		raise Exception("Must have a TTL")
	if not "msg_type" in message or message["msg_type"] not in MESSAGE_TYPES:
		raise Exception("Must have a valid msg_type")
	if forwarded and "msg_originator" not in message:
		raise Exception("Must have msg_originator in message if message was forwarded")

	message.update({
		"msg_forwarder": STATE["port"],
		"msg_id": STATE["msg_id"],
	})

	# If message originates from us, include that in the message
	if not forwarded: message.update({ "msg_originator": STATE["port"] })

	log_message(message=message, received=False)

	try:
		req = requests.post(
			"http://localhost:%d/receive" % peer,
			json=message
		)
	except requests.exceptions.RequestException as e:
		log_error(e)
	except ConnectionResetError as e:
		log_error(e)

	STATE["msg_id"] += 1

def log_message(message, received):
	logged = message.copy()
	logged.update({ "timestamp": time.time() })
	if received: logged.update({ "received": True })
	LOGS.append(logged)

def log_error(e):
	log_message(message={
		"error": str(e),
		"stack_trace": traceback.format_exc(),
	}, received=True)

@only_if_awake
def send_pings_to_everyone():
	'''
	Routine that runs every 5 seconds; sends pings to every peer.
	'''
	ping = {
		"msg_type": PING,
		"ttl":  0,
		"data": None,
	}

	for peer in [*STATE["peers"]]:
		send_message_to(peer=peer, message=ping, forwarded=False)

@only_if_awake
def evict_peers():
	'''
	Routine that evicts any peers who we haven't heard from in the last 10 seconds.
	Runs every second.
	'''
	current_time = time.time()
	peers_to_remove = [p for p in [*STATE["peers"]] if current_time - STATE["peers"][p] > 10]

	for peer in peers_to_remove:
		STATE["peers"].pop(peer)

@only_if_awake
def generate_and_gossip_next_mersenne_prime():
	'''
	Routine that generates the next Mersenne prime and gossips it to our peers.
	Runs every 10 seconds.
	'''
	new_prime = find_next_mersenne_prime(STATE["biggest_prime"])
	STATE["biggest_prime"] = new_prime
	STATE["biggest_prime_sender"] = MY_PORT

	prime_message = {
		"msg_type": PRIME,
		"ttl": 2,
		"data": new_prime,
	}

	for peer in [*STATE["peers"]]:
		send_message_to(peer=peer, message=prime_message, forwarded=False)

@app.route("/message_log")
def message_log():
	'''
	Reads out the last 5 messages logged by this node.
	'''
	return json.dumps(LOGS[-5:])

@app.route("/reset", methods=["POST"])
def reset():
	'''
	Hard reset on all state for this node. Still gets initialized to having
	the same bootstrap peer it started with.
	'''
	global AWAKE, LOGS, RECEIVED_MESSAGES, STATE
	AWAKE = True
	LOGS = []
	RECEIVED_MESSAGES = set()
	old_msg_id = STATE["msg_id"]
	STATE = {
		"name": MY_NAME,
		"port": MY_PORT,
		"peers": {},
		"biggest_prime": 2,
		"biggest_prime_sender": MY_PORT,
		"msg_id": old_msg_id + 1,
	}
	if len(sys.argv) >= 3: STATE["peers"][int(sys.argv[2])] = time.time()
	return "OK"

@app.route("/sleep", methods=["POST"])
def sleep():
	global AWAKE
	AWAKE = False
	return "OK"

@app.route("/wake_up", methods=["POST"])
def wake_up():
	global AWAKE
	AWAKE = True
	return "OK"

@app.route("/state")
def state():
	'''
	Reads out the current state of this node.
	'''
	return STATE

class Interval(Timer):
	def run(self):
		# Sleep a random period before starting, to add a bit of jitter between nodes
		time.sleep(random.uniform(0, 2))

		while not self.finished.wait(self.interval):
			try:
				self.function()
			except Exception as e:
				log_error(e)

if __name__ == "__main__":
	print("My name is %s" % MY_NAME)
	# If passed in another peer's port, initialize that peer
	if len(sys.argv) >= 3: STATE["peers"][int(sys.argv[2])] = time.time()

	# Send ping every 5 seconds
	ping_timer = Interval(5.0, send_pings_to_everyone)

	# Evict a peer if they haven't responded to a ping or sent a ping themselves
	eviction_timer = Interval(1.0, evict_peers)

	# Send a new Mersenne prime every 10 seconds
	prime_timer = Interval(10.0, generate_and_gossip_next_mersenne_prime)

	eviction_timer.start()
	ping_timer.start()
	prime_timer.start()
	serve(app, host="0.0.0.0", port=MY_PORT)
