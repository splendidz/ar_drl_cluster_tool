from s_action_mgr import S_ActionMgrInst
from s_waypoint_checker import S_WaypointCheckerInst
from action_space import CommandType
import utils


class S_WafefProcessingTimeChecker:
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_WafefProcessingTimeChecker()
        return cls._instance

    def __init__(self):
        self.moving_time_dict = {}  # key: waypoint, value: moving time [sec]
        self._waypoint_processtime: dict = {}  # key: waypoint, value: time
        self._accumulated_waypoint_processtime: dict = {0: 0}  # key: waypoint, value: accumulated time
        self._accumulated_moving_time: dict = {0: 0}
        self.last_waypoint = -1
        pass

    def set_waypoint_time(self, way_no, time_sec):
        if len(self.moving_time_dict) != 0:
            return

        self._waypoint_processtime[way_no] = time_sec
        if self.last_waypoint < way_no:
            self.last_waypoint = way_no

    def calculate(self, unit_list, transport_list):

        if len(self.moving_time_dict) != 0:
            return

        # accumulated processing time
        for key, val in self._waypoint_processtime.items():
            sum = 0
            for i in range(1, key + 1):
                sum += self._waypoint_processtime[i]
            self._accumulated_waypoint_processtime[key] = sum

        for i in range(1, self.last_waypoint):
            _, uname_from = S_WaypointCheckerInst.waypoint_units[i][0]
            _, uname_to = S_WaypointCheckerInst.waypoint_units[i + 1][0]

            tr_list_pick = S_ActionMgrInst.find_actions(CommandType.pick, uname_from)
            tr_list_place = S_ActionMgrInst.find_actions(CommandType.place, uname_to)

            assert len(tr_list_pick), f"There is no action that can pick from {uname_from}"
            assert len(uname_to), f"There is no action that can place from {uname_to}"

            tr_name = ""
            # find transport name which can pick and place from waypoint N and N+1
            for t1 in tr_list_pick:
                for t2 in tr_list_place:
                    if t1.tr_name == t2.tr_name:
                        tr_name = t1.tr_name
                        break
                if len(tr_name) != 0:
                    break

            assert len(uname_to), f"There is no transport that can pick & place from {uname_from} to {uname_to}"

            unit_from = None
            unit_to = None

            velocity_mmps = 1
            for t in transport_list:
                if t.Name == tr_name:
                    velocity_mmps = t._velocity
                    break

            for u in unit_list:
                if u.Name == uname_from:
                    unit_from = u
                    break
            for u in unit_list:
                if u.Name == uname_to:
                    unit_to = u
                    break

            pos_a = unit_from.position
            pos_b = unit_to.position

            sec = utils.calc_move_time_sec(pos_a, pos_b, velocity_mmps)
            sec = round(sec, 5)
            self.moving_time_dict[i + 1] = sec

        self._accumulated_moving_time[1] = 0

        for key, val in self.moving_time_dict.items():
            self._accumulated_moving_time[key] = self._accumulated_moving_time[key - 1] + val

    def get_processing_time(self, waypoint, include_last_process_time: bool) -> float:
        idx = waypoint if include_last_process_time else waypoint - 1
        sum_time = self._accumulated_waypoint_processtime[idx] + self._accumulated_moving_time[waypoint]
        return sum_time

    @property
    def done_time(self) -> float:
        sum_time = self._accumulated_waypoint_processtime[self.last_waypoint] + self._accumulated_moving_time[self.last_waypoint]
        return sum_time


S_WafefProcessingTimeCheckerInst = S_WafefProcessingTimeChecker.inst()
