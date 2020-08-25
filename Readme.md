python3 -m venv venv
source ./venv/bin/activate
pip install .

- update .env

source .env
export $(cut -d = -f 1 .env)
