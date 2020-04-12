pip3 install requirements.txt

python3 server.py 5000 &
python3 server.py 5001 5000 &
python3 server.py 5002 5001 &
python3 server.py 5003 5002

open frontend/index.html
