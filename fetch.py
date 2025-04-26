from typing import Literal, Union
import time
import requests
from dotenv import load_dotenv
from seleniumbase import SB
from os import getenv
from bs4 import BeautifulSoup
import json
from sbvirtualdisplay import Display

session = requests.Session()
load_dotenv()


def fetch_no_login(
    url: str,
    output_format: Literal["json", "text"] = "json",
    retry: int = 10,
    sleep_time_after_failing: int = 2,  # seconds
) -> Union[dict, str]:
    time.sleep(1)
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
            print(
                f"fetch_no_login() raise an exception '{e}'. Retries {retry_count} times"
            )
            time.sleep(sleep_time_after_failing * int(pow(2, retry_count)))


cache = dict()  # cache['url'] = {'data': ..., 'timestamp': ...}


def fetch_login(
    url: str,
    retry: int = 20,
    sleep_time_after_failing: int = 8,  # seconds
):
    # Check if cache hits
    if cache.get(url) and time.time() - cache[url]["timestamp"] < 5 * 60:
        return cache[url]["data"]
    # Fetch
    time.sleep(1)
    retry_count: int = 0
    display = Display(visible=0, size=(1440, 1880))
    display.start()
    while retry_count < retry:
        try:
            with SB(uc=True, locale="en") as sb:
                sb.activate_cdp_mode("https://atcoder.jp/login")
                sb.sleep(10)
                sb.uc_gui_click_captcha()  # uc_gui_click_cf()
                sb.sleep(2)
                sb.cdp.type("#username", getenv("ATCODER_USER_NAME"))
                sb.cdp.type("#password", getenv("ATCODER_PASSWORD"))
                sb.cdp.click("button[id=submit]")
                sb.sleep(5)
                sb.cdp.open(url)
                page_source = sb.cdp.get_page_source()
                soup = BeautifulSoup(page_source, "html.parser")
                pre_tag = soup.find("pre")
                if pre_tag is None:
                    raise ValueError("pre_tag must not be None")
                data = json.loads(pre_tag.text)
                # Store to cache
                cache[url] = {"data": data, "timestamp": time.time()}
                return data
        except Exception as e:
            retry_count += 1
            time.sleep(sleep_time_after_failing)
            print(e)
    display.stop()
