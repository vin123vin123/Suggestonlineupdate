import hashlib
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

SERVER_FILE = Path("server_logic.py")

# Initial logic (2 + 2 + 2)
INITIAL_CODE = '''# Version: Initial
def calculate():
    result = 2 + 2 + 2
    return f"Running Old Logic (2 + 2 + 2) = {result}"
'''

# Updated logic (3 + 3)
UPDATED_CODE_TEMPLATE = '''# Version: {date_str}
def calculate():
    result = 3 + 3
    return f"Running Updated Logic for {date_str} (3 + 3) = {{result}}"
'''

def check_and_update_server_file():
    """Updates the logic file on the server if the date has changed."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if SERVER_FILE.exists():
        content = SERVER_FILE.read_text(encoding="utf-8")
        # If today's date isn't in the file, update the logic
        if f"# Version: {today_str}" not in content:
            new_code = UPDATED_CODE_TEMPLATE.format(date_str=today_str)
            SERVER_FILE.write_text(new_code, encoding="utf-8")
            print(f"[SERVER] Updated {SERVER_FILE} with new logic for {today_str}!")

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the initial file with old logic (2 + 2 + 2) on startup
    if not SERVER_FILE.exists():
        SERVER_FILE.write_text(INITIAL_CODE, encoding="utf-8")
        print(f"[SERVER] Created initial {SERVER_FILE} with (2 + 2 + 2).")
    
    # Wait 15 seconds in this demo before applying the date-based update
    # so you have time to run the client once with the old logic!
    scheduler.add_job(check_and_update_server_file, "interval", seconds=15)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/check-update")
def check_update():
    """Returns the MD5 hash of the current server file so the client knows if it changed."""
    if not SERVER_FILE.exists():
        return {"exists": False}
    
    file_hash = hashlib.md5(SERVER_FILE.read_bytes()).hexdigest()
    return {"exists": True, "hash": file_hash}

@app.get("/download-logic")
def download_logic():
    """Sends the actual Python logic file to the client."""
    if not SERVER_FILE.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(path=SERVER_FILE, filename="app_logic.py")
