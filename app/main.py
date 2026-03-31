from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from app.speedtest import run_speedtest, init_db
import sqlite3
import os
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
init_db()

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()
# Run test every 60 minutes automatically
scheduler.add_job(run_speedtest, 'interval', minutes=60)
scheduler.start()

def get_latest_result():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "speedtest.db"))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results ORDER BY timestamp DESC LIMIT 1")
    latest = cursor.fetchone()
    conn.close()
    return latest


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    latest_data = get_latest_result()
    # Wandle das SQLite-Row-Objekt in ein echtes Dictionary um, falls Daten vorhanden sind
    context_data = dict(latest_data) if latest_data else None

    return templates.TemplateResponse(
        name="index.html",
        context={"request": request, "latest_data": context_data}
    )

@app.post("/api/run-test")
async def api_run_test():
    result = run_speedtest()
    # Ensure we return a JSON response with status, even on error
    if result and result.get("status") == "success":
        return JSONResponse(content=result)
    else:
        # Pass the error message back to the frontend
        error_msg = result.get("message", "Unknown error occurred.") if result else "Unknown error occurred."
        return JSONResponse(content={"status": "error", "message": error_msg}, status_code=400)

@app.get("/api/history")
async def api_history():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "speedtest.db"))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Letzte 24 Stunden holen (oder anpassen nach Bedarf)
    cursor.execute("SELECT * FROM results ORDER BY timestamp ASC")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content={"data": results})

@app.get("/api/download-csv")
async def download_csv():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "speedtest.db"))
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