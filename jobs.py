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
    get_avg_inner_perf_all_participants,
    update_rated_participants_perf,
)


def create_jobs_from_active_contests():
    contest_manager = ContestManager()
    contests: List[Contest] = contest_manager.new_contests()
    logger.info(f"There are {len(contests)} new active contests")
    for contest in contests:
        if not contest.is_rated:
            pass

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
            # Update aperf after the contest has started 5 minutes
            # Because Atcoder extends the 5-minute registration
            schedule.every(5).minutes.do(generate_data_algo_contest, contest=contest)


def dump_aperf_of_heuristic_participants(contest: Contest):
    """
    Download performance history of all participants into competition-history/heuristic
    then dump data/{contest}_avg_perf.json
    """
    logger.info(f"Updating data/{contest.short_name}_avg_perf.json file")
    aperfs = get_avg_inner_perf_all_participants(contest)
    dump_rank_to_perf(contest, aperfs)
    commit_to_github()


def dump_rounded_perf_of_all_into_a_file(contest: Contest):
    """
    Because to calculate rating in a heuristic contests, we need all performance history of each user
    After dumping the competition history of all participants into 'competition-history/{contest_type}/{username}.json
    put all of them into a file. The extension will fetch this file and then make prediction about rating.
    """
    logger.info(
        f"Creating {ALL_PARTICIPANTS_ROUNDED_PERF_HISTORY.format(contest.short_name)} file"
    )
    print(f"Dump the competition history of all participants in {contest.short_name} to a file")
    dump_rounded_perf_history_all_participants(contest)
    return schedule.CancelJob


def generate_data_algo_contest(contest: Contest) -> None | schedule.CancelJob:
    """
    Generate the average array of all participants (InnerPerformance)
    Calculate the performance array based on rank in contest
    Dump the competition history of all participants into a file (Performance)
    """
    logger.info(f"Generating data/{contest.short_name}_avg_perf.json file")
    aperfs = get_avg_inner_perf_all_participants(contest)
    dump_rank_to_perf(contest, aperfs)
    dump_rounded_perf_of_all_into_a_file(contest)
    commit_to_github()
    return schedule.CancelJob

# TODO: update not only the InnerPerformane, but Performance as well
def update_users_perf_based_on_final_result(
    contest: Contest,
) -> None | schedule.CancelJob:
    """
    Update the performance history of all rated participants by appending the performance in contest
    """
    if contest.hasFixedResult():
        update_rated_participants_perf(contest)
        commit_to_github()
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
    schedule.every(2).minutes.do(create_jobs_from_active_contests)
    while True:
        schedule.run_pending()
        time.sleep(1)
