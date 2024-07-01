import json
import schedule
import time
from typing import List
from constants import ALL_PARTICIPANTS_ROUNDED_PERF_HISTORY, CONTEST_TYPE_DUMP
from contest import ContestManager, Contest
from datetime import timedelta
from util import commit_to_github
from logger import logger
from performance import (
    dump_rounded_perf_history_all_participants,
    dump_rank_to_perf,
    fetch_perf,
    get_avg_inner_perf_all_participants,
    update_rated_participants_perf,
)


def create_jobs_from_contests_list():
    contest_manager = ContestManager()
    active_contests: List[Contest] = contest_manager.new_contests()
    logger.info(f"There are {len(active_contests)} new active contests")
    for contest in active_contests:
        if not contest.is_rated:
            continue

        schedule.every(30).seconds.do(dump_contest_type, contest=contest)
        # Update the participants's performance after the contest has finished
        schedule.every(3).hours.do(
            update_users_perf_based_on_final_result, contest=contest
        )

        if contest.type == "heuristic":
            # Update aperf every 5 minutes
            # TODO: need to be checked
            schedule.every(5).minutes.until(timedelta(seconds=contest.duration)).do(
                dump_aperf_of_heuristic_participants, contest=contest
            )
            # TODO: need to be checked
            schedule.every(5).minutes.until(timedelta(seconds=contest.duration)).do(
                dump_rounded_perf_of_all_into_a_file, contest=contest
            )

        elif contest.type == "algo":
            """
            Update aperf every 5 minutes until the contest ends from now.
            """
            generate_data_algo_contest(contest) # run intermediately
            schedule.every(5).minutes.until(timedelta(seconds=contest.duration)).do(
                generate_data_algo_contest, contest=contest
            )

    upcoming_contests: List[Contest] = contest_manager.upcoming_contests(
        timedelta_hours=1
    )
    # Get the performance history of participants 1 hour before the contest starts
    logger.info(
        f"{len(upcoming_contests)} upcoming contest(s) - {list(map(lambda ct: ct.short_name, upcoming_contests))}"
    )
    for contest in upcoming_contests:
        if not contest.is_rated:
            continue

        schedule.every().second.do(fetch_perf_participants, contest=contest)

    # logger.info(f"{len(schedule.get_jobs())} jobs are waiting to be executed.")
    logger.info(f"Current jobs list: {schedule.get_jobs()}")


def fetch_perf_participants(contest: Contest) -> schedule.CancelJob:
    fetch_perf(contest)
    return schedule.CancelJob


def dump_aperf_of_heuristic_participants(contest: Contest):
    """
    Download performance history of all participants into competition-history/heuristic
    then dump data/{contest}_avg_perf.json
    """
    logger.info(f"Updating data/{contest.short_name}_avg_perf.json file")
    aperfs = get_avg_inner_perf_all_participants(contest)
    dump_rank_to_perf(contest, aperfs)
    commit_to_github(f"Dump aperf of all participants of contest {contest.short_name}")


def dump_rounded_perf_of_all_into_a_file(contest: Contest):
    """
    Because to calculate rating in a heuristic contests, we need all performance history of each user
    After dumping the competition history of all participants into 'competition-history/{contest_type}/{username}.json
    put all of them into a file. The extension will fetch this file and then make prediction about rating.
    """
    logger.info(
        f"Creating {ALL_PARTICIPANTS_ROUNDED_PERF_HISTORY.format(contest.short_name)} file"
    )
    print(
        f"Dump the competition history of all participants in {contest.short_name} to a file"
    )
    dump_rounded_perf_history_all_participants(contest)
    return schedule.CancelJob


def generate_data_algo_contest(contest: Contest) -> None:
    """
    Generate the average array of all participants (InnerPerformance)
    Calculate the performance array based on rank in contest
    Dump the competition history of all participants into a file (Performance)
    """
    logger.info(f"Generating data/{contest.short_name}_avg_perf.json file")
    aperfs = get_avg_inner_perf_all_participants(contest)
    dump_rank_to_perf(contest, aperfs)
    dump_rounded_perf_of_all_into_a_file(contest)
    commit_to_github(f"Calculate the prediction data for {contest.short_name}")


def update_users_perf_based_on_final_result(
    contest: Contest,
) -> None | schedule.CancelJob:
    """
    Update the performance history of all rated participants by appending the performance in contest
    """
    if contest.hasFixedResult():
        update_rated_participants_perf(contest)
        commit_to_github(
            f"Update the performance of all participants - contest {contest.short_name}"
        )
        return schedule.CancelJob


def dump_contest_type(contest: Contest) -> None:
    """
    Dump the contest type into a file then commit to github
    Some contests have unusual names, such as "wtf19"
    So sometimes we can not determine the type of contests based on their names
    """
    with open(CONTEST_TYPE_DUMP.format(contest.short_name), "w") as f:
        json.dump({"type": contest.type}, f, indent=4)

    commit_to_github(f"Create contest type {contest.short_name}")
    return schedule.CancelJob


if __name__ == "__main__":
    schedule.every(2).minutes.do(create_jobs_from_contests_list)
    while True:
        schedule.run_pending()
        time.sleep(1)
