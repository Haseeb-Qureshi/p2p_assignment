#!/bin/bash

poetry update
poetry install

# Recompile frontend code
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
python3 server.py 5003 5002
