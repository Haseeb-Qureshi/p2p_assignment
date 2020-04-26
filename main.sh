#!/bin/bash

# Install Python dependencies
pip3 freeze > requirements.txt
pip3 install -r requirements.txt

# Recompile frontend code
npm install
npm run webpack

# Open website
open frontend/index.html

# Run 4 servers and kill all of them if one process is killed
killbg() {
        for p in "${pids[@]}" ; do
                kill "$p";
        done
}
trap killbg EXIT
pids=()
python3 server.py 5000 &
pids+=($!)
python3 server.py 5001 5000 &
pids+=($!)
python3 server.py 5002 5001 &
pids+=($!)
python3 server.py 5003 5002 &
pids+=($!)
python3 reverse_proxy.py 5004
