# Requirements

Install python
install uv: curl -LsSf https://astral.sh/uv/install.sh | sh 
Install requirements: uv pip install -r requirements.txt

Create .env file with your spotify credentials
```
SPOTIPY_CLIENT_ID=your_id
SPOTIPY_CLIENT_SECRET=app_secret
SPOTIPY_REDIRECT_URI='http://127.0.0.1:8888/callback'
```
Run script
