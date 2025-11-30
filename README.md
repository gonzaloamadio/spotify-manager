Install python 

install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Create venv: `uv venv --python 3.13`

Activate venv: `source .venv/bin/activate`

Install requirements: `uv pip install -r requirements.txt`

Create .env file with your spotify credentials
```
SPOTIPY_CLIENT_ID=your_id
SPOTIPY_CLIENT_SECRET=app_secret
SPOTIPY_REDIRECT_URI='http://127.0.0.1:8888/callback'
```

Run script: `python3 main.py`
