from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, Response
import uvicorn
import os
import sqlite3
import csv
import io
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from datetime import datetime
from app.speedtest import run_speedtest, init_db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "speedtest.db")


ROOT_DIR = os.path.dirname(BASE_DIR)
template_dir = os.path.join(ROOT_DIR, "templates")

templates = Jinja2Templates(directory=template_dir)


def scheduler_task():
    """Background task that runs the speedtest."""
    print("Background scheduler triggered a speedtest...")
    run_speedtest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts and stops background processes alongside the web server."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_task, "interval", seconds=60)
    scheduler.start()

    yield

    scheduler.shutdown()



app = FastAPI(title="Speedtest-Lite", lifespan=lifespan)
init_db()


def get_latest_result():
    """Connects to SQLite and gets the most recent test result."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM results ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


@app.get("/")
async def read_dashboard(request: Request):
    """Sends the HTML dashboard to the browser."""
    latest_data = get_latest_result()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"latest_data": latest_data}
    )

@app.post("/api/run-test")
async def api_run_test():
    """Endpoint to trigger a manual test via the frontend button."""
    result = run_speedtest()
    return JSONResponse(content={"status": "success", "data": result})


@app.get("/api/history")
async def api_get_history():
    """Returns data from last 24h, corrected for local timezone (UTC+2)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            datetime(timestamp, '+2 hours') as timestamp, 
            download, 
            upload 
        FROM results 
        WHERE timestamp >= datetime('now', '-24 hours')
        ORDER BY timestamp ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    history_data = [dict(row) for row in rows]
    return JSONResponse(content={"data": history_data})


@app.get("/api/download-csv")
async def download_csv():
    """Endpoint that generates a standard international CSV file with a dynamic timestamp filename."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, download, upload, ping FROM results ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=',')

    writer.writerow(["ID", "Timestamp", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"])
    writer.writerows(rows)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dynamic_filename = f"speedtest_history_{current_time}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dynamic_filename}"}
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)