from typing import List
from collections import defaultdict


class S_WaypointChecker:
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_WaypointChecker()
        return cls._instance

    def __init__(self):
        self.id_dict = defaultdict(list)
        self.name_dict = defaultdict(list)
        self.waypoint_units = defaultdict(list)
        self.locked = False
        # self._waypoint_processtime: dict = {}  # key: waypoint, value: time
        # self._waypoint_time_list: List[int] = []
        self.last_waypoint = 0

    def append_waypoint(self, unit_id, unit_name, way_no) -> bool:
        if self.locked:
            return False
        self.id_dict[unit_id].append(way_no)
        self.name_dict[unit_name].append(way_no)
        self.waypoint_units[way_no].append((unit_id, unit_name))
        # self._waypoint_processtime[way_no] = time_sec

        # max_way_no = max(self._waypoint_processtime.keys())
        # self._waypoint_time_list = [0] * (max_way_no + 1)
        # for key, value in self._waypoint_processtime.items():
        #    self._waypoint_time_list[key] = value

        if self.last_waypoint < way_no:
            self.last_waypoint = way_no

        return True

    # def get_process_times_waypoint_from(self, waypoint_from) -> float:

    #     time_sum = 0.0
    #     way_no = waypoint_from
    #     while way_no != len(self._waypoint_time_list):
    #         time_sum += self._waypoint_time_list[way_no]
    #         way_no += 1
    #     return time_sum

    # def get_process_times_waypoint_from_to(self, waypoint_from, waypoint_to) -> float:

    #     time_sum = 0.0
    #     for i in range(waypoint_from, waypoint_to + 1):
    #         time_sum += self._waypoint_time_list[i]

    #     return time_sum

    def lock(self):
        self.locked = True

    def check_waypoint_to_place_by_id(self, unit_id, waypoint_to_place) -> bool:
        for i in self.id_dict[unit_id]:
            if i == waypoint_to_place + 1:
                return True
        return False

    def check_waypoint_to_place_by_name(self, unit_name, waypoint_to_place) -> bool:
        for i in self.name_dict[unit_name]:
            if i == waypoint_to_place + 1:
                return True
        return False


S_WaypointCheckerInst = S_WaypointChecker.inst()
