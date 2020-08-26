## SennderTest

### Installation

Install and activate a new Python virtual environment:
```bash
python3 -m venv .venv
source ./venv/bin/activate
pip install .
```

Setup a redis test server for example with a docker image (caching)

Set the values inside `.env`

Load environment variables (or add these commands to `.venv/bin/activate`):  
```bash
source .env
export $(cut -d = -f 1 .env)
```

### Usage

Launch the app locally with:  
```bash
cd senndertest
python manage.py runserver
```
