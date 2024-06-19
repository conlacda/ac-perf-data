import subprocess
from bs4 import BeautifulSoup
from typing import List
from tqdm import tqdm
from os import getenv
import argparse
from fetch import fetch
from dotenv import load_dotenv
from constants import ACTIVE_USERS_URL, CONTEST_TYPE
from performance import dump_rounded_perf_of_all_into_a_file, fetch_user_perf
from util import commit_to_github
from logger import logger


def number_active_users_page(contest_type: CONTEST_TYPE) -> int:
    html = fetch(ACTIVE_USERS_URL[contest_type], "text")
    soup = BeautifulSoup(html, features="html.parser")
    ul = soup.select_one(".pagination.pagination-sm.mt-0.mb-1")
    last_li = ul.select_one("li:last-child")
    return int(last_li.text)


def resolve_users_on(contest_type: CONTEST_TYPE, page=1) -> None:
    html = fetch(f"{ACTIVE_USERS_URL[contest_type]}&page={page}", "text")
    source = BeautifulSoup(html, features="html.parser")
    users: List[str] = [item.text for item in source.select("a.username")]

    for user in tqdm(users):
        perfs = fetch_user_perf(user, contest_type)
        dump_rounded_perf_of_all_into_a_file(user, perfs, contest_type)


def setup() -> None:
    load_dotenv()
    subprocess.run(
        [
            "git",
            "remote",
            "set-url",
            "origin",
            f"https://conlacda:{getenv('GITHUB_TOKEN')}@github.com/conlacda/ac-competition-history.git",
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        choices=["algo", "heuristic"],
        help="Specify type of contest you want to get data",
        required=True,
    )
    parser.add_argument(
        "--start_page",
        type=int,
        nargs="?",
        default=1,
        help="The start page number to process",
    )

    args = parser.parse_args()
    contest_type: CONTEST_TYPE = args.type
    start_page = args.start_page

    setup()

    logger.info(f"Getting data of {args.type} contests")
    last_page: int = number_active_users_page(contest_type)
    logger.info(f"There are {last_page} pages\n")
    for page in range(start_page, last_page + 1):
        logger.info(f"Getting data of page {page}")
        resolve_users_on(contest_type, page)
        commit_to_github()
