import os, shutil, subprocess, tempfile, glob, json
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

app = FastAPI()
TOKEN = os.environ["API_TOKEN"]
COOKIES = "/cookies/cookies.txt"  # optional, only used if the file exists

class Req(BaseModel):
    url: str

def check(tok):
    if tok != TOKEN:
        raise HTTPException(401, "bad token")

def base_cmd():
    cmd = ["yt-dlp", "--no-playlist"]
    if os.path.exists(COOKIES):
        cmd += ["--cookies", COOKIES]
    return cmd

@app.post("/info")
def info(req: Req, x_token: str = Header(None)):
    check(x_token)
    r = subprocess.run(base_cmd() + ["-J", "--no-download", req.url],
                       capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise HTTPException(400, r.stderr[-500:])
    d = json.loads(r.stdout)
    return {"title": d.get("title"), "description": d.get("description"),
            "uploader": d.get("uploader"), "duration": d.get("duration")}

@app.post("/download")
def download(req: Req, x_token: str = Header(None)):
    check(x_token)
    tmp = tempfile.mkdtemp()
    r = subprocess.run(
        base_cmd() + ["-f", "mp4/best", "--merge-output-format", "mp4",
                      "-o", f"{tmp}/video.%(ext)s", req.url],
        capture_output=True, text=True, timeout=300)
    files = glob.glob(f"{tmp}/video.*")
    if r.returncode or not files:
        shutil.rmtree(tmp, ignore_errors=True)
        raise HTTPException(400, r.stderr[-500:])
    return FileResponse(files[0], media_type="video/mp4", filename="video.mp4",
                        background=BackgroundTask(shutil.rmtree, tmp, True))


import secrets, time, requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
STORE = "/data/videos"
BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://dl.nahgil.fr")
os.makedirs(STORE, exist_ok=True)

class StoreReq(BaseModel):
    file_path: str

@app.post("/store")
def store(req: StoreReq, x_token: str = Header(None)):
    check(x_token)
    if not BOT_TOKEN:
        raise HTTPException(500, "bot token not set")
    if ".." in req.file_path or not req.file_path.startswith(("videos/", "documents/")):
        raise HTTPException(400, "bad file path")
    now = time.time()
    for f in glob.glob(f"{STORE}/*.mp4"):
        if now - os.path.getmtime(f) > 14 * 86400:
            os.remove(f)
    name = secrets.token_urlsafe(16) + ".mp4"
    r = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{req.file_path}",
                     stream=True, timeout=120)
    if r.status_code != 200:
        raise HTTPException(400, "telegram download failed")
    with open(f"{STORE}/{name}", "wb") as out:
        for chunk in r.iter_content(1 << 20):
            out.write(chunk)
    return {"url": f"{BASE_URL}/v/{name}"}

@app.api_route("/v/{name}", methods=["GET", "HEAD"])
def serve(name: str):
    if "/" in name or ".." in name:
        raise HTTPException(404)
    path = f"{STORE}/{name}"
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4")
