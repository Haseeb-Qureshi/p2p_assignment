#!/bin/bash

# Install Python dependencies
poetry install

# Recompile frontend code
npm install
npm run webpack

# Run 4 nodes and kill all of them if one process is killed
killbg() {
        for p in "${pids[@]}" ; do
                kill "$p";
        done
}
python3 -m webbrowser "http://localhost:5000"

trap killbg EXIT
pids=()
python3 node.py 5001 &
pids+=($!)
python3 node.py 5002 5001 &
pids+=($!)
python3 node.py 5003 5002 &
pids+=($!)
python3 node.py 5004 5003 &
pids+=($!)
python3 backendy_stuff/reverse_proxy.py 5000
