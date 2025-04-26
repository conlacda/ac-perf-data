from contest import Contest, ContestManager
from main import generate_performance_files, update_users_perf_based_on_final_result


contest = Contest(
    "2024-05-12 21:00:00+0900",
    "Ⓐ◉AtCoder Regular Contest agc072",
    "/contests/agc072",
    "03:00",
    "2000 -",
)

generate_performance_files(contest)
# update_users_perf_based_on_final_result(contest)

# contest = Contest(
#     "2024-05-29 21:00:00+0900",
#     "Ⓗ◉ Toyota Programming Contest 2024#5(AtCoder Heuristic Contest ahc041)",
#     "/contests/ahc041",
#     "04:00",
#     "All"
# )
# print(contest.short_name)

generate_performance_files(contest)
# # dump_aperf_of_heuristic_participants(contest)
# # dump_rounded_perf_of_all_into_a_file(contest)
# update_users_perf_based_on_final_result(contest)

# contestManager = ContestManager()
# print(contestManager.contest_list())
