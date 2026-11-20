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
