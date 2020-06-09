# P2P Protocol Exercise

## Background
In this assignment, you'll be building a simple P2P protocol inspired by [**GIMPS**, the Great Internet Mersenne Prime Search](https://en.wikipedia.org/wiki/Great_Internet_Mersenne_Prime_Search). GIMPS is a distributed computing project that lets anyone in the world to contribute their computing power to help discover new prime numbers. It was founded in 1996 and is still running to this day.

GIMPS is credited with having discovered the largest currently known prime number: **2⁸²⁵⁸⁹⁹³³ - 1** (this prime has 24,862,048 digits in decimal).

GIMPS only searches for [Mersenne primes](https://en.wikipedia.org/wiki/Mersenne_prime). Mersenne primes are prime numbers that are one less than a power of 2 (i.e., 2ᴺ - 1). GIMPS focuses on these because Mersenne primes possess mathematical properties that make them easy for computers to generate and test.

The real GIMPS is not actually P2P (it uses a central server to coordinate all of the volunteer computers), but in our version, we'll be making a toy P2P version.

You will be writing all of your code in `node.py`.

## What this protocol does
At a high level, here's what the protocol looks like: we'll have 4 nodes that all slowly generate increasing Mersenne primes. Every 10 seconds, each node tries to generate the next largest Mersenne prime compared to any it's seen so far. It then gossips that new prime to its peers. Each node will keep track of who has generated the largest Mersenne prime so far.

Each node will live on a different port. You will identify each node by its port number (e.g., node 5001, node 5002, etc.).

Zooming in now, each node in this protocol is continually running four core routines:
1. Every 10 seconds, it generates a new Mersenne prime that is larger than any Mersenne prime it has seen so far. It then gossips that new Mersenne prime to its peers.
2. Every 1 second, it evicts any `stale` peers from its peer list. A peer is `stale` if a node hasn't heard from that peer in the last 10 seconds (judged by its last-heard timestamp).
3. Every 5 seconds, it pings each of the peers in its peer list to check whether they're still alive.

The three above routines are already implemented in the code. All nodes will automatically do them.

The fourth routine governs how nodes respond when they receive a message—what they do in respond to a ping or a gossip message. This is the core of the P2P protocol. **You will be implementing this routine from scratch.**

You'll notice that when you start the nodes, they quickly evict all of their peers and stop talking to each other. This is because they're not processing any messages from each other. It's up to you to fix this.

## The message types
There are three message types in this protocol.
* `PING`: a point-to-point message that checks if a peer is still alive and responsive. This message has a TTL of 0, meaning it does not get forwarded.
* `PONG`: a point-to-point message that is sent in response to a `PING`. This also has a TTL of 0.
* `PRIME`: a new Mersenne Prime. This is the only message in the protocol that gets gossiped and forwarded. This will have an initial TTL of 2 in our system, meaning it gets forwarded twice before dying off.

## The `respond` routine
When we respond to a message, depending on the message, we should do the following:
* Whenever we receive a message, we should update the last-heard timestamp of whichever node forwarded us that message. In the code, this node is called the **msg_forwarder**.
* We should also check whether we've already seen this message (via the `RECEIVED_MESSAGES` set)
  - If we've already seen it, we should not forward or process the message.
  - If we we've never seen it, we should record it in the set of all received messages, and then go ahead and process the message.
* If the message is a `PING`:
  - We should respond to the sender with a `PONG` message with a TTL of 0 (so the `PONG` doesn't get gossiped further)
* If the message is a `PONG`:
  - This means someone is responding to our `PING`. We shouldn't need to do anything further after having updated the last-heard timestamp.
* If the message is a `PRIME`:
  - This means that the originating node found a new Mersenne prime and gossiped it out.
  - If the prime number is bigger than our current largest seen prime number:
    - We should update our largest seen prime number (stored in our `STATE`)
    - We should also update the largest prime sender to be the person who generated this prime—this is referred to in code as the **msg_originator**. We store the largest prime sender in our `STATE`. We want to be sure we're attributing credit to the person who found the prime number, rather than just whoever gossiped it to us.
  - We should add the **msg_originator** to our peer list and update their timestamp, since the `PRIME` message is the only message in this protocol that actually gets forwarded (`PING`s and `PONG`s are point-to-point messages only). `PRIME`s are the only way we can ever populate our peer list with new peers.
  - If the `PRIME` message has a TTL greater than 0:
    - We should forward the message on to each of our peers (**making sure to decrement its TTL by 1**)
      - You'll need to do this by generating a new message with identical parameters, but with a decreased TTL, and then sending that message to each of your peers.

To send a message, you'll need to call the `send_message_to()` function. It takes three arguments:
* `peer (int)`: The peer you're sending to
* `message (dict)`: The message you're sending, encoded as a dict (e.g., { "msg_type": "PONG", "ttl": 0, "data": None })
* `forwarded (bool)`: Whether or not this message has been forwarded to you from someone else (so we know whether to mark you as the message originator)

Example: `send_message_to(peer=5002, message={"msg_type": "PRIME", "ttl": 1, "data": 17}, forwarded=True)`

Once you get all of this wired up, you should be able to see all of the nodes generating Mersenne primes in concert, just like the real GIMPS! (Mostly.)

You'll know it's working when all of the nodes are peered with each other and they all generally agree on who generated the most recent prime. (They will sometimes disagree on who discovered the latest prime first due to race conditions, but this is to be expected in a P2P protocol!)

## The message format
Each message that your node receives will be pre-parsed for you (this is handled in the `receive` function, which forwards the parameters to your `respond` function), so you don't have to worry about parsing.

Each message in this protocol has 6 parameters:

* `msg_type (str)`: `"PING"`, `"PONG"`, or `"PRIME"`
* `msg_id (int)`: The auto-incrementing message counter for each node. This allows you to dedupe messages.
* `msg_forwarder (int)`: The port of the immediate node that sent/forwarded you this message.
* `msg_originator (int)`: The port of the node that created the original message (for a 0 TTL point-to-point message like a `PING`, this will be the same as the forwarder).
* `ttl (int)`: Time-to-live; the number of hops remaining in the lifetime of this message until it should be no longer be forwarded. A 0 TTL message should not be forwarded any further.
* `data (None or int)`: The data in the message payload. For `PING`s and `PONG`s, this will be `None`. For a PRIME message, the data field will be the prime number.

## Setup (on repl.it)
It should be simple to run the application on repl.it. First navigate to https://repl.it/@nakamoto/p2passignment and hit the `fork` button at the top. That will give you your own cloned version of the repo. Then hit the `run ▶` button at the top, which should run the setup script (`bash replit_setup.sh`).

This will launch the P2P dashboard and run 4 node servers in tandem. From here, you can start writing your server code in `node.py` and re-running the setup script to see how it affects node behavior.

Once you've edited the node code and want to re-start the system, hit CTRL+C to kill the nodes and just hit the `restart ⟳` button (or you can manually run `bash replit_setup.sh`). This should restart the setup script.

*Note that due to constraints of repl.it, the frontend JS code does not get re-compiled in the setup script. If you want to edit the frontend code, you will have to do it manually by replacing frontend/dist/main.js with the contents of your updated JS. If you need to transpile it first, you can use https://babeljs.io/repl.*

## Setup (running locally)
There are five prerequisites to run this locally:

* bash
* Python3
* NodeJS
* npm (NodeJS package manager)
* poetry (Python package manager)

These may be tricky to get installed on Windows; if you want to try, Google some installation instructions for each. On UNIX-based systems (Linux or MacOS) these should be straightforward to install.

To set up and run the project, run `bash main.sh`. This should install prerequisites, recompile the JS, spin up 4 nodes, run the reverse proxy, and open a browser window for the dashboard. If you edit node code, you should spin down the servers (CTRL+C) and restart the script.

(If you're having trouble setting it up, I'd encourage you to use the repl.it version for now.)

## Tips
* Before you start coding, I recommend reading through the current codebase. It should be relatively straightforward to understand.
* Before you write any code, notice how nodes behave: they quickly forget about each other and every node ends up isolated. This is because they're ignoring each other's heartbeats.
    * First, make it so when we receive a message from someone, we update when we last heard from them. This will prevent nodes from falling off the face of the earth.
* Next, make sure that when you receive a `PRIME` message, you update when you last heard from the originator of the `PRIME` message. That should daisy-chain together the network so it's fully connected.
* Then you want to make sure that when you receive a `PING` message, you're properly responding with a `PONG` message!
* Finally, you'll need to implement proper gossip forwarding on `PRIME` messages. Follow the logic as explained earlier in this document.

## Debugging
* The frontend was primarily tested in Google Chrome, so if you are running into frontend bugs, try running it in Chrome.
* Open the node dashboard in a separate window from your coding interface. This will make your life a lot easier.
* If you want to surface messages to the node dashboard, you can use `log_message(message={"your message": "here"}, received=True)` to make it show up in the node logs.
    * To make it even more pronounced, you can use `log_error("Some text here")`, though this will clog up the interface more dramatically.
* The button on the right of the node logs should let you copy the node logs to the clipboard. You can then dump it into a text editor and comb through it at your own pace to try to debug.
* You shouldn't need any extra state in order to get this protocol working. But if you want to add some more for yourself, any fields you add to the `STATE` variable will automatically get displayed on the frontend.
* You may occasionally run into concurrency-related race conditions (this will manifest as editing an array or dictionary while it's being iterated over). This can be fixed with some locking, but I decided to leave it as is so the code is easier to follow and understand.
    * These errors should be rare. If your code generally isn't working, it's probably not due to a concurrency bug.

## Want something harder?
Switch to the git branch `hard`. This will require you to implement more of the core P2P functionality. If you're using repl.it, you can access it [here](https://repl.it/@nakamoto/p2passignment-hard-mode), or if you're running it locally you can just check out the `hard` branch.

(If you want *really hard mode*, try rewriting the entire P2P protocol from scratch. Consider this only if you have the free time and some experience debugging distributed systems! I'd recommend using a simple web server like Flask (Python), Sinatra (Ruby), or http-server (NodeJS). If you want to be really hardcore, you can try to manually write messages directly to TCP sockets on localhost.)

## Solution
Take the time and try to build this! The only real way to build intuitions about how P2P systems work is through debugging them. But if you've finished and just want to see a canonical solution, you can check out the repo's [solution branch](https://github.com/Haseeb-Qureshi/p2p_assignment/tree/solution).
