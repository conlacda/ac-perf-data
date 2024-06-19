import subprocess
from bs4 import BeautifulSoup
from typing import List, Literal
import json
from tqdm import tqdm
from os import path, getenv
import argparse
from fetch import fetch
from dotenv import load_dotenv
from constants import ACTIVE_USERS_URL, COMPETITION_HISTORY_URL, CONTEST_TYPE


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
        save_user_competition_performance(user, contest_type)


def save_user_competition_performance(
    username: str, contest_type: CONTEST_TYPE
) -> None:
    rated_peformance = get_rated_competition_performance(username, contest_type)
    with open(f"competition-history/{contest_type}/{username}.json", "w") as json_file:
        json.dump(rated_peformance, json_file)


def get_rated_competition_performance(
    username: str, contest_type: CONTEST_TYPE
) -> List[int]:
    data = fetch(COMPETITION_HISTORY_URL[contest_type].format(username), "json")
    # Keep only inner performance
    rated_peformance = []
    for item in data:
        if item.get("IsRated"):
            rated_peformance.append(item.get("InnerPerformance"))
    return rated_peformance


def commit_to_github() -> None:
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "auto commit"])
    subprocess.run(["git", "push"])


def setup() -> None:
    load_dotenv()
    subprocess.run(
        [
            "git",
            "remote",
            "set-url",
            "origin",
            f"https://conlacda:{getenv('GITHUB_TOKEN')}@github.com/conlacda/ac-perf-data.git",
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

    print(f"Getting data of {args.type} contests")
    last_page: int = number_active_users_page(contest_type)
    print(f"There are {last_page} pages\n")
    for page in range(start_page, last_page + 1):
        print(f"Getting data of page {page}")
        resolve_users_on(contest_type, page)
        commit_to_github()
