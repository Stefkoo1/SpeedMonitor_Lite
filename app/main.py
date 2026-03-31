from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn
import os

app = FastAPI(title="SpeedMonitor-Lite")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=template_dir)

@app.get("/")
async def read_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
