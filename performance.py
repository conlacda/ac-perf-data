from constants import (
    ALL_PARTICIPANTS_COMPETITION_HISTORY,
    AVG_PERF_DUMP,
    COMPETITION_HISTORY_URL,
    CONTEST_TYPE,
    PERF_BY_RANKING,
    RESULT_URL,
)
from typing import List
import json
from os import path
from contest import Contest
from fetch import fetch
from tqdm import tqdm
from logger import logger
import math


def load_saved_perf(username: str, contest_type: CONTEST_TYPE) -> List[int]:
    with open(f"competition-history/{contest_type}/{username}.json", "r") as f:
        return json.load(f)


def dump_participants_aperf(data: dict, contest: Contest) -> None:
    f = open(AVG_PERF_DUMP[contest.type].format(contest.short_name), "w")
    json.dump(data, f, indent=4)
    f.close()

# This function is only for the heuristic contests.
# Because to calculate rating of an user in the heuristic contests we need all competition history
# not last as the algo contests
def dump_participants_competition_history(data: dict, contest: Contest) -> None:
    f = open(ALL_PARTICIPANTS_COMPETITION_HISTORY.format(contest.short_name), "w")
    json.dump(data, f)
    f.close()

def average_performance_of_user(username: str, contest: Contest):
    perf_arr = load_saved_perf(username, contest.type)
    if len(perf_arr) == 0:
        return contest.new_comer_aperf

    perf_arr.reverse()
    numerator: float = 0
    denominator: float = 0
    for i in range(len(perf_arr)):
        numerator += pow(0.9, i + 1) * perf_arr[i]
        denominator += pow(0.9, i + 1)
    return numerator / denominator


def fetch_user_perf(username: str, contest_type: CONTEST_TYPE) -> List[int]:
    # Fetch from atcoder
    data = fetch(COMPETITION_HISTORY_URL[contest_type].format(username), "json")
    rated_peformance = []
    for item in data:
        if item.get("IsRated"):
            rated_peformance.append(item.get("InnerPerformance"))
    return rated_peformance


def dump_user_perf(
    username: str, rated_peformance: List[int], contest_type: CONTEST_TYPE
) -> None:
    with open(f"competition-history/{contest_type}/{username}.json", "w") as json_file:
        json.dump(rated_peformance, json_file)


# Update aperf after the contest has the fixed result
def update_rated_participants_perf(contest: Contest) -> None:
    res = fetch(RESULT_URL.format(contest.short_name), "json")
    for item in res:
        if item.get("IsRated"):
            # results api does not return InnerPerformance
            # if user has Performance is the max performance, then get InnerPerformance from user's competition history
            # otherwise, just update InnerPerformance by Performance
            username: str = item.get("UserScreenName")
            contest_perf = item.get("Performance")
            # If someone joins the contest at the last minute and has no the perf history file.
            # Their perf history should be fetched from Atcoder
            if contest_perf == contest.max_perf or not path.exists(
                f"competition-history/{contest.type}/{username}.json"
            ):
                perfs = fetch_user_perf(username, contest.type)
                dump_user_perf(username, perfs, contest.type)
            else:
                perfs = load_saved_perf(item.get("UserScreenName"), contest.type)
                perfs.append(contest_perf)
                dump_user_perf(username, perfs, contest.type)


def generate_aperf_for_participants(contest: Contest) -> List[float]:
    participants: List[str] = contest.get_participants(only_rated=True)
    logger.info(f"{len(participants)} rated users joined {contest.short_name}")

    # Download the competition performance of participant if not exists
    print("Download the competition history of all participants")
    for participant in tqdm(participants):
        if not path.exists(f"competition-history/{contest.type}/{participant}.json"):
            perfs = fetch_user_perf(participant, contest.type)
            dump_user_perf(participant, perfs, contest.type)

    # Generate avg_perf at data/{contest_name}_avg_perf.json
    data: dict[str, float] = {}
    print("Calculate average performance of every participants")
    for participant in tqdm(participants):
        data[participant] = average_performance_of_user(participant, contest)

    # Actually, we dont need to dump this file. Just for checking if the result prediction gets wrong.
    dump_participants_aperf(data, contest)

    # Return the list of aperf (in order to calculate performance during contest)
    return data.values()

# From the avg of all users, calculate the performance X of user with ranking r using binary search
def gen_perf_by_ranking(contest: Contest, aperfs: List[float]) -> None:
    # Calculate performance for each ranking
    logger.info(f"Calculating the performance table of contest {contest.short_name}")
    perf_during_contest: List[int] = [] * len(aperfs)
    n = len(aperfs)
    print(f"Calculate performance based on ranking in the contest {contest.short_name} (binary search)")

    def perf2Rank(perf):
        ans = 0
        for aperf in aperfs:
            ans += 1 / (1 + pow(6.0, (mid - aperf) / 400.0))
        ans += 0.5
        return math.ceil(ans)

    for i in tqdm(range(n)):
        r = i + 1
        left = -5000
        right = 7000
        while left < right:
            mid = (left + right) // 2

            if perf2Rank(mid) <= r:
                right = mid
            else:
                left = mid + 1

        assert left == right
        while calRank(left) < r:
            left -= 1
        
        perf_during_contest.append(min(left, contest.max_perf))

    # Dump to file
    f = open(PERF_BY_RANKING[contest.type].format(contest.short_name), "w")
    json.dump(perf_during_contest, f)
    f.close()

    return perf_during_contest

def dump_competition_history_of_all_participants(contest: Contest) -> None:
    participants: List[str] = contest.get_participants(only_rated=True)

    # Get the list of participants, then fetch the competition history of users if it does not exist.
    data: dict[str, List[int]] = {}
    print(f"Generate the competition history of participants in contest {contest.short_name}")
    for participant in tqdm(participants):
        if not path.exists(f'competition-history/{contest.type}/{participant}.json'):
            perfs = fetch_user_perf(participant, contest.type)
            dump_user_perf(participant, perfs, contest.type)

        perfs = load_saved_perf(participant, contest.type)
        data[participant] = perfs

    dump_participants_competition_history(data, contest)
