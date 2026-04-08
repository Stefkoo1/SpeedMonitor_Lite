from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from app.speedtest import run_speedtest
from app.database import init_db, DB_PATH
import sqlite3
import os
import csv
from io import StringIO
from datetime import datetime, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Config from environment ---
INTERVAL_MINUTES = int(os.getenv("SPEEDTEST_INTERVAL_MINUTES", "60"))
COOLDOWN_SECONDS = int(os.getenv("MANUAL_TEST_COOLDOWN_MINUTES", "5")) * 60

# --- Database init ---
init_db()

# --- Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(run_speedtest, 'interval', minutes=INTERVAL_MINUTES)
scheduler.start()

# --- Server-side cooldown state ---
_last_manual_test: datetime | None = None


def get_cooldown_remaining() -> int:
    """Returns remaining cooldown in seconds, 0 if no cooldown active."""
    if _last_manual_test is None:
        return 0
    elapsed = (datetime.now() - _last_manual_test).total_seconds()
    return max(0, int(COOLDOWN_SECONDS - elapsed))


def get_latest_result():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results ORDER BY timestamp DESC LIMIT 1")
    latest = cursor.fetchone()
    conn.close()
    return latest


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    latest_data = get_latest_result()
    context_data = dict(latest_data) if latest_data else None
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "latest_data": context_data,
            "interval_minutes": INTERVAL_MINUTES,
        }
    )


@app.get("/api/status")
async def api_status():
    """Returns current cooldown state — polled by frontend on page load."""
    remaining = get_cooldown_remaining()
    return JSONResponse(content={
        "cooldown_active": remaining > 0,
        "cooldown_remaining_seconds": remaining,
        "cooldown_total_seconds": COOLDOWN_SECONDS,
    })


@app.post("/api/run-test")
async def api_run_test():
    global _last_manual_test

    # Server-side cooldown check
    remaining = get_cooldown_remaining()
    if remaining > 0:
        return JSONResponse(
            content={"status": "cooldown", "remaining": remaining,
                     "message": f"Bitte warte noch {remaining}s bevor du einen neuen Test startest."},
            status_code=429
        )

    result = run_speedtest()

    if result and result.get("status") == "success":
        # Only start cooldown after a successful test
        _last_manual_test = datetime.now()
        return JSONResponse(content=result)
    else:
        # On error: allow retry after 60s instead of full cooldown
        _last_manual_test = datetime.now() - timedelta(seconds=COOLDOWN_SECONDS - 60)
        error_msg = result.get("message", "Unbekannter Fehler.") if result else "Unbekannter Fehler."
        return JSONResponse(content={"status": "error", "message": error_msg}, status_code=400)


@app.get("/api/history")
async def api_history():
    """Returns results from the last 24 hours."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM results WHERE timestamp >= datetime('now', '-24 hours') ORDER BY timestamp ASC"
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content={"data": results})


@app.get("/api/download-csv")
async def download_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, download, upload, ping FROM results ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(["ID", "Timestamp", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"])
    writer.writerows(rows)

    response = StreamingResponse(iter([csv_file.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=speedtest_history.csv"
    return response
