# Recompile frontend code
npm install
npm run webpack

# Install Python dependencies
poetry install

# Run 4 nodes and kill all of them if one process is killed
killbg() {
        for p in "${pids[@]}" ; do
                kill "$p";
        done
}
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
python3 reverse_proxy.py 5000
