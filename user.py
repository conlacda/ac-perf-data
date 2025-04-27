from datetime import datetime, timezone, timedelta
import json
import os
from typing import List, Literal
from constants import COMPETITION_HISTORY, COMPETITION_HISTORY_URL
from contest import Contest, ContestManager
from fetch import fetch


class User:
    username: str

    def __init__(self, username):
        self.username = username

    def __str__(self) -> str:
        return f"User: {self.username}"

    # Lấy ra performance trung bình của 1 user
    # Áp dụng cho cả algo và heuristic
    # Note: hiện tại hàm tính performance trung bình của từng người dùng đang đúng
    # Performance tính bằng binary search đang lệch +- 5 điểm (Đang sai lệch): TODO
    # Khi có performance, dựa vào lịch sử thi đấu tính rating đang đúng
    def average_inner_performance(self, contest: Contest):
        chistory: dict[str, List[int]] = self.competition_history(contest.type)
        perf_arr = chistory['InnerPerformance']

        if len(perf_arr) == 0:
            return contest.new_comer_aperf

        perf_arr.reverse()
        numerator: float = 0
        denominator: float = 0
        for i in range(len(perf_arr)):
            numerator += pow(0.9, i + 1) * perf_arr[i]
            denominator += pow(0.9, i + 1)
        return numerator / denominator
    
    # Chạy cho heuristic contest - ko dùng tới - phần này client dùng chứ ko có ở server
    # def decayedPerformance(self, competion_history: dict[str, List[int]]) -> List[float]:
    #     competion_num = len(competion_history['InnerPerformance'])
    #     result: List[float] = []
    #     for i in range(competion_num):
    #         datetime1 = datetime.strptime(competion_history['ContestEndTime'][i], "%Y-%m-%d %H:%M:%S") + timedelta(hours=9) # UTC+0->UTC+9
    #         datetime2 = datetime.strptime(competion_history['ContestEndTime'][competion_num], "%Y-%m-%d %H:%M:%S") + timedelta(hours=9)
    #         diff = datetime2.date() - datetime1.date()
    #         result.append(competion_history['InnerPerformance'][i] + 150 - 100 * diff.days / 365)

    #     return result

    def fetch_competition_history(self, contest_type: str):
        # Lấy dữ liệu lịch sử thi đấu của 1 người dùng với contest_type từ trên Atcoder xuống.
        """
        @return
        dict {
            'RoundedPerformance': [100, 2400, ...],
            'InnerPerformance': [100, 3000, ...],
            'ContestEndTime': [t1, t2, ...],
            'Weight": [0.5 | 1, 0.5 | 1, ...],
            'ContestShortName': ['abc123', 'agc012', ...]
        }
        """
        data = fetch(
            COMPETITION_HISTORY_URL[contest_type].format(self.username), "json"
        )
        result: dict[str, List[int]] = {
            "RoundedPerformance": [],
            "InnerPerformance": [],
            "ContestEndTime": [],
            "Weight": [],
            "ContestShortName": [],
        }
        contestManager = ContestManager()
        for item in data:
            if item.get("IsRated"):
                ContestShortName = item.get("ContestScreenName").split(".")[0]
                result["RoundedPerformance"].append(item.get("Performance"))
                result["InnerPerformance"].append(item.get("InnerPerformance"))
                endTime = (
                    datetime.fromisoformat(item.get("EndTime"))
                    .astimezone(timezone.utc)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )
                # datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S') - convert it back to datetime object
                result["ContestEndTime"].append(endTime)
                if contest_type == "algo":
                    result["Weight"].append(1)
                else:
                    contest = contestManager.find_contest(ContestShortName)
                    result["Weight"].append(contest["weight"])
                result["ContestShortName"].append(ContestShortName)
        return result

    # Lưu lại lịch sử performance của người dùng
    def save_performance_history(self, data: dict[str, List[int]], contest_type: str):
        file = COMPETITION_HISTORY.format(contest_type=contest_type, username=self.username)
        with open(file, "w") as f:
            json.dump(data, f, default=str)

    def competition_history(
        self, contest_type: Literal["algo", "heuristic"], refresh: bool = False
    ):
        # Lấy ra lịch sử thi đấu của người dùng, nếu chưa có thì fetch từ Atcoder xuống
        # refresh = True: luôn fetch từ Atcoder xuống (do dữ liệu hiện tại đã cũ - số lần thi đầu ở local != Competitions tại API)
        """
        @return dict {
            'InnerPerformance': [],
            'RoundedPerformance': [],
            'ContestEndTime': [],
            'Weight': [],
            'ContestShortName': []
        }
        """
        file = COMPETITION_HISTORY.format(contest_type=contest_type, username=self.username)
        if not os.path.exists(file) or refresh:
            perfs = self.fetch_competition_history(contest_type)
            self.save_performance_history(perfs, contest_type)
            return perfs

        with open(f"competition-history/{contest_type}/{self.username}.json", "r") as f:
            return json.load(f)


    # So sánh nếu số lần tham gia contest lấy từ Atcoder và local khác nhau thì xóa file vì dữ liệu ko khớp
    def removeIfHistoryObsolete(self, competition_num: int, contest_type: Literal["algo", "heuristic"]):
        file = COMPETITION_HISTORY.format(contest_type=contest_type, username=self.username)
        if os.path.exists(file):
            local_competition_history = self.competition_history(contest_type)
            if (len(local_competition_history.get("RoundedPerformance")) != competition_num):
                print(f"Remove obsolete history file {file}")
                os.remove(file)
