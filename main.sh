pip3 install requirements.txt

open frontend/index.html

trap 'kill %1; kill %2' SIGINT
python3 server.py 5000 | tee 0.log | sed -e 's/^/[Peer0] /' & python3 server.py 5001 5000 | tee 1.log | sed -e 's/^/[Peer1] /' & python3 server.py 5002 5001 | tee 2.log | sed -e 's/^/[Peer2] /' & python3 server.py 5003 5002 | tee 3.log | sed -e 's/^/[Peer3] /'
