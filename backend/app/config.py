import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
MUSIC_DIR = os.path.join(DATA_DIR, "music")
COVERS_DIR = os.path.join(DATA_DIR, "covers")
DATABASE_PATH = os.path.join(DATA_DIR, "database.sqlite")

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

SECRET_KEY = os.getenv("RHYME_SECRET_KEY", "rhyme-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

UPLOAD_MAX_SIZE_MB = 50
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a"}

GITHUB_CLIENT_ID = os.getenv("RHYME_GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("RHYME_GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("RHYME_GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")

ADMIN_GITHUB_IDS = [
    int(x) for x in os.getenv("RHYME_ADMIN_GITHUB_IDS", "").split(",") if x.strip().isdigit()
]

CORS_ORIGINS = os.getenv(
    "RHYME_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://rhyme.rhyme17.top",
).split(",")

for d in (DATA_DIR, MUSIC_DIR, COVERS_DIR):
    os.makedirs(d, exist_ok=True)
