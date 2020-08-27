# SennderTest

## Local Installation

- This app requires a *redis server* for caching than can be set with a docker image !
- Install the app inside a new Python virtual environment.
```bash
python3 -m venv .venv
source ./venv/bin/activate
pip install .
```


## Common Installation

- Set the values inside `.env`
- Load environment variables (or add these commands to `.venv/bin/activate`):  
```bash
source .env
export $(cut -d = -f 1 .env)
```


## Usage

Launch the app locally with:  
```bash
cd senndertest
python manage.py runserver
```


## Development Installation

If you want to improve the app and develop, follow the next steps

- Setup a redis server for test
- Install the app inside a new Python virtual environment with `dev` dependencies
```bash
python3 -m venv .venv
source ./venv/bin/activate
pip install -e .[dev]
```

From here on follow instructions from `Common Installation`


## Test

To test the app (from project root):
```bash
source ./venv/bin/activate
cd senndertest
coverage run --source="." manage.py test senndermovies
```
