from typing import Literal, Union
import time
import requests
from dotenv import load_dotenv
from seleniumbase import SB
from os import getenv
from bs4 import BeautifulSoup
import json
import threading
import queue
import sys

session = requests.Session()
load_dotenv()
q = queue.Queue()


# Hàm fetch này sử dụng request để fetch
# Sử dụng cho các url ko cần xác minh captcha
# Với url cần xác minh captcha, sử dụng hàm bên dưới
def fetch(
    url: str,
    output_format: Literal["json", "text"] = "json",
    retry: int = 10,
    sleep_time_after_failing: int = 2,  # seconds
) -> Union[dict, str]:
    time.sleep(0.7)
    retry_count: int = 0
    while retry_count < retry:
        try:
            res = session.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                return res.json() if output_format == "json" else res.content
            else:
                raise Exception(
                    f"Fetch failed with status {res.status_code} - {res.reason}"
                )
        except Exception as e:
            retry_count += 1
            print(f"fetch() raise an exception '{e}'. Retries {retry_count} times")
            time.sleep(sleep_time_after_failing * int(pow(2, retry_count)))


fetchedData = dict()  # fetchedData['url'] = {'data': ..., 'timestamp': ...}


def requestForFetch(url: str):
    q.put(url)


def getRequestedData(url: str):
    cnt: int = 0
    while cnt < 10:
        if fetchedData.get(url) and time.time() - fetchedData[url]["timestamp"] < 5 * 60:
            return fetchedData[url]["data"]
        time.sleep(5)
        cnt += 1
    return None


def fetchWithBrowser(retry: int = 15):
    with SB(uc=True, locale="en") as sb:
        for _ in range(retry):
            sb.activate_cdp_mode("https://atcoder.jp/login")
            sb.sleep(10)
            sb.uc_gui_click_captcha(retry=True)
            sb.sleep(2)
            sb.cdp.type("#username", getenv("ATCODER_USER_NAME"))
            sb.cdp.type("#password", getenv("ATCODER_PASSWORD"))
            sb.cdp.click("button[id=submit]")
            sb.sleep(5)
            page_title = sb.get_page_title()
            print(page_title)
            if page_title.startswith("AtCoder"):
                print(f"Login OK ({_}/{retry}) :3")
                break
            else:
                print(f"Login failed ({_}/{retry}) :(")
                if _ == retry - 1:
                    sys.exit("Login failed!!!")

        while True:
            requestedUrl = q.get()
            sb.cdp.open(requestedUrl)
            page_source = sb.cdp.get_page_source()
            soup = BeautifulSoup(page_source, "html.parser")
            pre_tag = soup.find("pre")
            if pre_tag is None:
                return None  # fetch fails
            data = json.loads(pre_tag.text)
            # Store to cache
            fetchedData[requestedUrl] = {"data": data, "timestamp": time.time()}
        
# def fetchWithBrowser():

#     with sync_playwright() as p:
#         browser = p.firefox.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#         page.goto("https://atcoder.jp/login")

#         while True:
#             requestedUrl = q.get()
#             response = page.goto(requestedUrl)
#             data = response.json()
#             fetchedData[requestedUrl] = {"data": data, "timestamp": time.time()}

# fetchWithBrowserThread = threading.Thread(target=fetchWithBrowser)
# fetchWithBrowserThread.start()
