# SpeedMonitor-Lite — CLAUDE.md

## Projektübersicht

Leichtgewichtige Web-App zur automatischen Netzwerkgeschwindigkeitsmessung.
Stack: FastAPI + Jinja2 (Backend), Chart.js (Frontend), SQLite (Storage), APScheduler (Automatisierung), ndt7-client (Messmotor).

## Projektstruktur

```
SpeedMonitor_Lite/
├── app/
│   ├── main.py          # FastAPI-App, Scheduler, API-Endpunkte
│   ├── speedtest.py     # Messlogik (ndt7-client), DB-Schreiboperationen
│   └── database.py      # init_db() – wird aktuell nicht von main.py genutzt
├── templates/
│   └── index.html       # Dashboard (Jinja2 + Chart.js, Dark Mode)
├── Dockerfile           # Multi-stage Build: golang:alpine → python:3.11-alpine
├── requirements.txt     # fastapi, uvicorn, jinja2, apscheduler
└── CLAUDE.md
```

## Anforderungen & Implementierungsstand

### Must-Have (M)

| ID | Anforderung | Status | Hinweis |
|----|-------------|--------|---------|
| M1 | Speed test (Download / Upload / Ping) | Implementiert | `speedtest.py` via `ndt7-client` |
| M1 | Konfigurierbares Intervall | Offen | Hardcoded auf 60 min (`main.py:22`) – kein ENV-Var, kein UI-Regler |
| M2 | Persistente SQLite-Datenbank | Implementiert | `app/speedtest.db`, Tabelle `results` |
| M3 | Dashboard – aktuelles Ergebnis | Implementiert | Server-side via Jinja2 |
| M3 | Dashboard – 24h-Graph | Teilweise | `/api/history` liefert ALLE Einträge, kein 24h-Filter |
| M4 | Docker (Alpine / Proxmox-kompatibel) | Implementiert | Multi-stage mit `python:3.11-alpine` |

### Should-Have (S)

| ID | Anforderung | Status | Hinweis |
|----|-------------|--------|---------|
| S1 | "Run Test Now"-Button | Implementiert | Mit Spinner-Zustand & Fehlerbehandlung |
| S2 | CSV-Export | Implementiert | `GET /api/download-csv` |
| S3 | Responsive Design | Teilweise | Flexbox + Viewport-Meta vorhanden, keine Media Queries |

## Bekannte Mängel / Offene Punkte

1. **M1 – Intervall nicht konfigurierbar**: Der Scheduler ist auf 60 Minuten hardcoded (`main.py:22`).
   - Fix: `SPEEDTEST_INTERVAL_MINUTES` als ENV-Variable auslesen, im Dockerfile als `ENV` setzen.

2. **M3 – 24h-Filter fehlt**: `/api/history` gibt alle gespeicherten Ergebnisse zurück.
   - Fix: SQL-Query auf `WHERE timestamp >= datetime('now', '-24 hours')` einschränken.

3. **S3 – Responsive unvollständig**: Kein explizites Breakpoint-CSS für mobile Ansichten.
   - Fix: Media Queries für `max-width: 600px` hinzufügen (Cards auf `flex-direction: column`).

4. **Code-Duplizierung `init_db()`**: Funktion existiert in `database.py` und `speedtest.py`.
   - Fix: `database.py` als Single Source of Truth, Import in `speedtest.py`.

## API-Endpunkte

| Method | Path | Beschreibung |
|--------|------|--------------|
| GET | `/` | Dashboard (HTML) |
| POST | `/api/run-test` | Speedtest sofort starten |
| GET | `/api/history` | JSON-History (aktuell: alle Einträge) |
| GET | `/api/download-csv` | CSV-Export aller Einträge |

## Lokale Entwicklung

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
docker build -t speedmonitor-lite .
docker run -d -p 8000:8000 -v speedtest_data:/code/app speedmonitor-lite
```

> Volume mounten (`-v`), damit `speedtest.db` Container-Neustarts überlebt.
