from flask import Flask, request
import schedule
import time
import threading
from os import path
from datetime import datetime

from jobs import create_jobs_from_active_contests

app = Flask(__name__)


# Function to run the scheduled tasks
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/")
def index():
    day = request.args.get("date")
    logs_file = "logs.txt"
    if day is not None:
        logs_file = f"logs.txt.{datetime.now().strftime('%Y-%m-%d')}"
    if not path.exists(logs_file):
        f = open(logs_file, "a")
        f.close()

    with open(logs_file, "r") as f:
        return f.readlines()


if __name__ == "__main__":
    schedule.every(2).minutes.do(create_jobs_from_active_contests)
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    app.run()
