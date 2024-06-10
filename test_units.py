from contest import Contest
from jobs import (
    generate_algo_aperf,
    dump_aperf_of_heuristic_participants,
    dump_all_participants_competition_history_in_a_file,
    update_users_perf_based_on_final_result,
)


contest = Contest(
    "2024-05-12 21:00:00+0900",
    "Ⓐ◉AtCoder Regular Contest arc179",
    "/contests/arc179",
    "01:40",
    "- 2799",
)

# generate_algo_aperf(contest)
# update_users_perf_based_on_final_result(contest)

# contest = Contest(
#     "2024-05-29 21:00:00+0900",
#     "Ⓗ◉ Toyota Programming Contest 2024#5(AtCoder Heuristic Contest 033)",
#     "/contests/ahc033",
#     "240:00",
#     "All"
# )
# dump_aperf_of_heuristic_participants(contest)
# dump_all_participants_competition_history_in_a_file(contest)
# update_users_perf_based_on_final_result(contest)
