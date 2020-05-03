# P2P Protocol Exercise

## Background
In this assignment, you'll be building a simple P2P protocol inspired by [GIMPS, the Great Internet Mersenne Prime Search](https://en.wikipedia.org/wiki/Great_Internet_Mersenne_Prime_Search). GIMPS is a distributed computing project that lets anyone in the world to contribute their computing power to help discover new prime numbers. It was founded in 1996 and is still running to this day. GIMPS is credited with having discovered the largest currently known prime number: **2<sup>82,589,933</sup> - 1**.

This prime number is a [Mersenne prime](https://en.wikipedia.org/wiki/Mersenne_prime). Mersenne primes are prime numbers are primes that are 1 less than a power of 2 (i.e., primes of the form **2<sup>N</sup> - 1**). GIMPS focuses on Mersenne primes because they possess mathematical properties that make them easy for computers to generate and test.

The real GIMPS is not actually P2P (it uses a central server to coordinate all of the volunteers), but in our version, we'll be making it fully P2P.

## What this protocol does

In this protocol, each node runs four core routines:
1. Every 10 seconds, it will generate a new Mersenne prime that is larger than any Mersenne prime it has seen so far
    * It will then gossip that new Mersenne prime to its peers
2. Every 1 second, it will evict any `stale` peers from its peer list
    * A peer is `stale` if a node hasn't heard from that peer in the last 10 seconds (judged by its last-heard timestamp)
3. Every 5 seconds, it will ping each of the peers in its peer list

The three above routines are already implemented.

The fourth routine is how nodes respond when they receive a message. **You will be implementing this routine.**

## The `respond` routine
When we respond to a message, depending on the message, we should do the following:
* Whenever we receive a message, we should update the last-heard timestamp of whoever forwarded us that message—the **message forwarder**
* If the message is a `PING`:
  - We should respond to the sender with a `PONG` message with a TTL of 0 (so the `PONG` doesn't get gossiped further)
* If the message is a `PONG`:
  - We shouldn't need to do anything further beyond updating the last-heard timestamp
* If the message is a `PRIME`:
  - This means that the originating node found a new Mersenne prime and gossiped it out (via routine 1)
  - If the prime number is bigger than our current largest seen prime number:
    - We should update our largest seen prime number (stored in our `STATE`)
    - We should also update the largest prime sender to be the person who generated this prime—the **message originator**. This is also stored in our `STATE`. We want to be sure we're attributing credit to the person who found the prime number, rather than just whoever gossiped it to us.
  - We should add the **message originator** to our peer list and update their timestamp, since the `PRIME` message is the only message in this protocol that actually gets forwarded (`PING`s and `PONG`s are point-to-point messages only), so `PRIME`s are the only way we can ever populate our peer list with new peers
  - If the `PRIME` message has a TTL greater than 0:
    - We should forward the message on to each of our peers (**making sure to decrement its TTL by 1**)
      - You'll need to do this

## The message format


## Setup (on repl.it)

## Setup (running locally)

## What to do

## Recommended steps

## Want hard mode?
