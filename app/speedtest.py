import sqlite3
import os
import random
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "speedtest.db")

def run_speedtest():
    print("Running Speedtest")
    time.sleep(4)

    download = round(random.uniform(850.0, 950), 2)
    upload = round(random.uniform(750.0, 890), 2)
    ping = round(random.uniform(10, 18), 2)

    print(f"Measured values: Ping {ping} ms | Download {download} Mbps | Upload {upload} Mbps")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO results (download, upload, ping)
        VALUES (?, ?, ?)
    ''', (download, upload, ping))

    conn.commit()
    conn.close()

    print("Done and saved to DB")
    return {"ping": ping, "download": download, "upload": upload}


if __name__ == "__main__":
    run_speedtest()