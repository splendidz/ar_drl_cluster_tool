import random
from sim_classes import EQState
import copy
from collections import defaultdict
from sim_classes import SimUnit, SimLoadPort, Wafer
from s_simulator_config import S_SimConfInst


class S_InitStateMgr:
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_InitStateMgr()
        return cls._instance

    def __init__(self):
        self.env_handles = {}
        self.initialized = False
        self.init_state_ori = []
        self.random_set_count = 0

    def initialize(self, state_obj: EQState):
        if self.initialized:  # init once
            return

        self.initialized = True
        self.random_set_count = S_SimConfInst.random_init_state_count

        waypoint_dict = defaultdict(list)
        for unit in state_obj._unit_list:
            unit: SimUnit = unit
            if unit._unit_type == "loadport":
                continue
            waypoint_dict[unit._waypoint_list[0]].append(unit)
        waypoint_dict = dict(sorted(waypoint_dict.items()))

        if S_SimConfInst.init_full_wafer == False and self.random_set_count > 0:
            for i in range(self.random_set_count):
                random_units = defaultdict(list)
                # extract two random units
                for wayno, unit_list in waypoint_dict.items():
                    if wayno % 2 == 0:
                        random_units[wayno].extend(random.sample(unit_list, 2))

                self.init_state_ori.append(random_units)

        elif S_SimConfInst.init_full_wafer:
            full_units = defaultdict(list)
            for wayno, unit_list in waypoint_dict.items():
                full_units[wayno].extend(unit_list)

            self.init_state_ori.append(full_units)

    def create_handle(self) -> int:
        handle = len(self.env_handles) + 1
        self.env_handles[handle] = copy.deepcopy(self.init_state_ori)

        return handle

    def make_init_state(self, handle, init_state_obj: EQState):

        if S_SimConfInst.random_init_state_count == 0 and S_SimConfInst.init_full_wafer == False:
            return

        samples: list = self.env_handles[handle]
        random.seed(42)
        random_units: defaultdict = random.choice(samples)
        samples.remove(random_units)  # remove chosen item to choice left items nextime.

        # if choose all items, copy again.
        if len(samples) == 0:
            self.env_handles[handle] = copy.deepcopy(self.init_state_ori)

        loadport: SimLoadPort = self.find_loadport(init_state_obj)

        for wayno, unit_list in reversed(random_units.items()):
            for unit in unit_list:
                unit: SimUnit = self.find_unit(unit.Name, init_state_obj)
                wafer: Wafer = loadport.take_out_wafer()
                wafer.waypoint = wayno - 1
                unit.put_in_wafer(wafer)
                unit._time_required = 0  # set wafer as current processing done
                unit.time_elapsed(0)  # update state

    def find_unit(self, unit_name: str, state_obj: EQState):
        for unit in state_obj._unit_list:
            if unit.Name == unit_name:
                return unit
        assert False, f"cannot find unit [{unit_name}]."

    def find_loadport(self, state_obj: EQState):
        for unit in state_obj._unit_list:
            if unit._unit_type == "loadport":
                return unit
        assert False, f"cannot find loadport."


S_InitStateMgrInst = S_InitStateMgr.inst()
