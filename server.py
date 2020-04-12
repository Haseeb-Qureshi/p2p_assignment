from flask import Flask, request
from flask_cors import CORS
from threading import Timer, RLock
from primes import find_next_mersenne_prime
import time
import functools
import traceback
import sys
import json
import requests
import random
import ipdb # TODO:REMOVE

if len(sys.argv) < 2: raise Exception("Must pass in port number")

MY_PORT = int(sys.argv[1])
if MY_PORT < 1024: raise Exception("Port number must be >= 1024")

# Randomly choose a human-readable name
names = open("names.txt", "r").read().split("\n")
MY_NAME = random.choice(names)

# Settings
RANDOM_DISCONNECTS = False
INFECTION_FACTOR = 2

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

# List of all messages we've received from peers
MESSAGE_HISTORY = []

# Global state object for reading and altering state: you should read and write to this
STATE = {
	"name": MY_NAME,
	"port": MY_PORT,
	"peers": {}, # (key: port number, value: timestamp when we last heard from them)
	"biggest_prime": 2, # Biggest Mersenne prime we've seen so far (starts at 2)
	"biggest_prime_sender": MY_PORT, # Sender of the current biggest prime (starts as self)
	"msg_id": 0, # Monotonically increasing message counter (we'll automatically increment this for you)
}

def only_if_awake(f):
	@functools.wraps(f)
	def if_awake(*args, **kwargs):
		if AWAKE:
			return f(*args, **kwargs)
		else:
			return "Asleep"
	return if_awake

def respond(msg_type, msg_id, msg_forwarder, msg_source, ttl, data):
	STATE["peers"][msg_source] = time.time()

	if msg_type == PING: # received a ping
		pong_message = {
			"msg_type": PONG,
			"ttl": 0,
			"data": None,
		}

		send_message_to(message=pong_message, peer=msg_source)
	elif msg_type == PONG: # received a pong
		pass
	elif msg_type == PRIME: # got a prime number from someone
		if data > STATE["biggest_prime"]: # new biggest prime
			STATE["biggest_prime"] = data
			STATE["biggest_prime_sender"] = msg_source

		if ttl == 0: return

		message = {
			"msg_type": PRIME,
			"ttl": ttl - 1,
			"data": data,
		}

		for peer in STATE["peers"].keys():
			send_message_to(peer=peer, message=message)

@only_if_awake
@app.route("/receive", methods=["POST"])
def receive():
	req_data = request.get_json()
	log_message(message=req_data, received=True)

	msg_type = req_data["msg_type"]
	msg_id = req_data["msg_id"]
	msg_forwarder = request.getRemoteAddr()
	msg_source = req_data["msg_source"]
	ttl = int(req_data["ttl"])
	data = req_data["data"]

	try:
		respond(msg_type, msg_id, msg_forwarder, msg_source, ttl, data)
	except Exception as e:
		log_error(e)

	return "OK"

@only_if_awake
def send_message_to(peer, message):
	'''
	Send point-to-point message to a specific peer. Node-specific metadata is
	automatically added. Only one message is sent out at a time to avoid
	race conditions.
	'''
	if type(peer) is not int:
		raise TypeError("Tried to send a message to non-integer: %d" % peer)
	if not "ttl" in message:
		raise Exception("Must have a TTL")
	if not "msg_type" in message or message["msg_type"] not in MESSAGE_TYPES:
		raise Exception("Must have a valid msg_type")

	message.update({
		"msg_source": STATE["port"],
		"msg_id": STATE["msg_id"],
	})

	log_message(message=message, received=False)

	try:
		req = requests.post(
			"http://localhost:%d/receive" % peer,
			json=message
		)
	except requests.exceptions.RequestException as e:
		log_error(e)

	STATE["msg_id"] += 1

@only_if_awake
def send_pings_to_everyone():
	ping = {
		"msg_type": PING,
		"ttl":  0,
		"data": None,
	}

	for peer in STATE["peers"].keys():
		send_message_to(peer=peer, message=ping)

@only_if_awake
def gossip_prime_number(prime):
	prime_message = {
		"msg_type": PRIME,
		"ttl": 2,
		"data": prime,
	}

	k = min(INFECTION_FACTOR, len(STATE["peers"]))
	for peer in random.sample(STATE["peers"].keys(), k):
		send_message_to(peer=peer, message=prime_message)

def log_message(message, received):
	logged = message.copy()
	logged.update({ "timestamp": time.time() })
	if received: logged.update({ "received": True })
	MESSAGE_HISTORY.append(logged)

def log_error(e):
	log_message(message={
		"error": str(e),
		"stack_trace": traceback.format_exc(),
	}, received=True)

@only_if_awake
def evict_peers():
	'''
	Evicts any peers who we haven't heard from in the last 10 seconds.
	'''
	current_time = time.time()
	peers_to_remove = [p for p in STATE["peers"].keys() if current_time - STATE["peers"][p] > 10]

	for peer in peers_to_remove:
		STATE["peers"].pop(peer)

@only_if_awake
def generate_next_mersenne_prime():
	'''
	Generates the next Mersenne prime and gossips it to our peers.
	Runs once every 10 seconds, but then waits a random period <5s to stagger node timing.
	'''
	time.sleep(random.uniform(0, 5))

	new_prime = find_next_mersenne_prime(STATE["biggest_prime"])
	STATE["biggest_prime"] = new_prime
	STATE["biggest_prime_sender"] = MY_PORT
	gossip_prime_number(new_prime)

@app.route("/message_log")
def message_log():
	'''
	Reads out the last 5 messages received by this node.
	'''
	return json.dumps(MESSAGE_HISTORY[-5:])

@app.route("/")
def state():
	'''
	Reads out the current state of this node.
	'''
	return STATE

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

@app.route("/dump")
def dump():
	import faulthandler
	faulthandler.enable()
	faulthandler.dump_traceback(file=open('tracestack.log', 'w+'), all_threads=True)
	return "OK"

class Interval(Timer):
	def run(self):
		while not self.finished.wait(self.interval): self.function()

if __name__ == "__main__":
	print("My name is %s" % MY_NAME)
	# If passed in another peer's port, initialize that peer with no message history
	if len(sys.argv) >= 3: STATE["peers"][int(sys.argv[2])] = time.time()

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
