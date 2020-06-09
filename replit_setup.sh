echo "This script will take several seconds to boot."
echo "To kill all of the nodes, hit CTRL+C."
echo "To restart the setup script, run the command: bash replit_setup.sh"
echo "---------------------------------------------------------------------"

pkill -f "python3"

# Run 4 nodes and kill all of them if one process is killed
killbg() {
        for p in "${pids[@]}" ; do
                kill "$p";
        done
}
trap killbg EXIT
pids=()
python3 node.py 5000 &
pids+=($!)
python3 node.py 5001 5000 &
pids+=($!)
python3 node.py 5002 5001 &
pids+=($!)
python3 node.py 5003 5002
pids+=($!)
