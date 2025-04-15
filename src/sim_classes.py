from collections import deque, defaultdict
from overrides import overrides
from typing import Dict, List, Any, Tuple, cast, Generator
import utils
from utils import pos3d
from action_space import CommandType, SingleAction, CommandType
from state_tensors import TransportInfo, UnitInfo, EQState
from abc import ABC, abstractmethod
import copy
import random
from s_simulator_config import S_SimConfInst
from error_code import ActionResult


class ITimeElapsable:

    @abstractmethod
    def time_elapsed(self, timestep) -> float:
        """process timestep and returns left timestep."""
        pass


#####################################
##
## Wafer
##
class Wafer:
    def __init__(self, id: int, waypoint: int):
        self.id = id
        self.done = False
        self.trajectory = dict()
        self.waypoint = waypoint
        """
        trajectory of units and transports with each timespan. \n
        > key: unit or transport name. \n
        > value: timespan at the position.
        """

    def record_trajectory(self, name, elapsed):
        if name in self.trajectory:
            self.trajectory[name] += elapsed
        else:
            self.trajectory[name] = elapsed

    def to_string(self, prefix=""):
        d = [f"{key}[span={val}]" for key, val in self.trajectory.items()]
        d = ", ".join(d)
        return f"{prefix}id={self.id}, trajectory=({d})"


#####################################
##
## SimUnit
##
class SimUnit(UnitInfo, ITimeElapsable):
    """Single unit object data"""

    def __init__(self, id: int, name: str, unit_type: str, process_timespan: float, pos: pos3d):
        super().__init__(pos)
        self._id: int = id
        self._NAME: str = name
        self._unit_type: str = unit_type
        self._PROECSS_TIMESPAN: float = process_timespan
        """ The needed time for the process."""
        self._wafer: Wafer = None
        self._waypoint_list: List[int] = []
        self._pending_time = 0

    @property
    def ID(self):
        return self._id

    @property
    def Name(self):
        return self._NAME

    @property
    def busy(self) -> bool:
        return self._time_required != 0

    @property
    def has_wafer(self) -> bool:
        return self._wafer != None

    @property
    def is_full(self) -> bool:
        return self.has_wafer

    @property
    def ready_to_pick(self) -> bool:
        return self._ready_to_pick

    @property
    def ready_to_place(self) -> bool:
        return self._ready_to_place

    @property
    def get_pending_time(self) -> float:
        return self._pending_time

    def get_wafer_gen(self) -> Generator[Wafer, None, None]:
        yield self._wafer

    def reset(self):

        # variables
        self._time_required = 0.0
        self._curr_waypoint_no = 0
        self._ready_to_pick = False
        self._ready_to_place = False
        self._wafer: Wafer = None

        # constant values #
        # self._pos
        # self._id
        # self._NAME
        # self._PROECSS_TIMESPAN
        # self._waypoint_list: List[int] = []

    def set_waypoint_list(self, waypoint_no):
        self._waypoint_list.append(waypoint_no)

    def check_waypoint_to_place(self, waypoint_to_place) -> bool:
        for i in self._waypoint_list:
            if i == waypoint_to_place + 1:
                return True
        return False

    def take_out_wafer(self) -> Wafer:
        assert self._wafer != None
        w = self._wafer
        self._wafer = None
        self._wafer_id = 0
        # self._wafer_count = 0
        self.time_elapsed(0)  # update status
        return w

    def top_wafer(self) -> Wafer:
        assert self._wafer != None
        return self._wafer

    def put_in_wafer(self, wafer: Wafer):
        assert self._wafer == None and self._time_required == 0, "wafer exists"
        self._wafer = wafer
        self._wafer.waypoint += 1
        self._curr_waypoint_no = wafer.waypoint
        self._wafer_id = wafer.id
        # self._wafer_count = 1
        # self._time_required = self._PROECSS_TIMESPAN
        self._time_required = self._PROECSS_TIMESPAN * random.uniform(0.9, 1.1)
        self.time_elapsed(0)  # update status

    # implementation of abstract
    def time_elapsed(self, timestep) -> float:

        self._time_required -= timestep
        self._time_required = max(self._time_required, 0.0)

        self._ready_to_pick = self.has_wafer and self._time_required == 0.0
        self._ready_to_place = self.has_wafer == False and self._time_required == 0.0

        if self._ready_to_pick:
            self._pending_time += timestep
        else:
            self._pending_time = 0

        if self.has_wafer == False:
            self._curr_waypoint_no = 0

        # write the time spent.
        if self._wafer != None and timestep > 0:
            self._wafer.record_trajectory(self._NAME, timestep)

        return self._time_required

    def to_string(self, prefix=""):
        str_wafer = "None"
        if self._wafer != None:
            str_wafer = self._wafer.to_string()
        s = f"{prefix}ID={self.ID}, Name={self.Name}, time_required={self._time_required}, ready_to_pick={self._ready_to_pick}, ready_to_place={self._ready_to_place}\n    {prefix}Wafer={str_wafer}"
        return s


##
## SimAirlockExit
##
class SimAirlock(SimUnit):

    def take_out_wafer(self) -> Wafer:
        assert self._wafer != None
        w = self._wafer
        self._wafer = None
        self._wafer_id = 0
        # self._wafer_count = 0
        self._time_required = self._PROECSS_TIMESPAN * random.uniform(0.9, 1.1)  # to make vacuum or atmosphere
        self.time_elapsed(0)  # update status
        return w

    def put_in_wafer(self, wafer: Wafer):
        assert self._wafer == None and self._time_required == 0, "wafer exists"
        self._wafer = wafer
        self._wafer.waypoint += 1
        self._curr_waypoint_no = wafer.waypoint
        self._wafer_id = wafer.id
        # self._wafer_count = 1
        # self._time_required = self._PROECSS_TIMESPAN
        self._time_required = self._PROECSS_TIMESPAN * random.uniform(0.9, 1.1)  # to make vacuum or atmosphere
        self.time_elapsed(0)  # update status


#####################################
##
## SimBufferSlots
##
# class SimBufferSlots(SimUnit):

#     def __init__(self, id, name, unit_type: str, capacity: int, process_timespan, pos):
#         super().__init__(id=id, name=name, unit_type=unit_type, capacity=capacity, process_timespan=process_timespan, pos=pos)
#         self._wafer_qu: deque[Wafer] = deque(maxlen=capacity)

#     @property
#     def is_full(self) -> bool:
#         return len(self._wafer_qu) == self._wafer_qu.maxlen

#     @property
#     def capacity(self) -> int:
#         return self._wafer_qu.maxlen

#     @property
#     def wafer_count(self) -> int:
#         return len(self._wafer_qu)

#     @overrides
#     def get_wafer_gen(self) -> Generator[Wafer, None, None]:
#         for wafer in self._wafer_qu:
#             yield wafer

#     def reset(self):
#         SimUnit.reset(self)
#         self._wafer_qu.clear()

#     @overrides
#     def time_elapsed(self, timestep) -> float:

#         self._time_required -= timestep
#         self._time_required = max(self._time_required, 0.0)

#         if timestep > 0:
#             for wafer in self._wafer_qu:
#                 if wafer != None and wafer.done == False:
#                     wafer.record_trajectory(self._NAME, timestep)

#         self._ready_to_pick = self._time_required == 0.0 and self.wafer_count > 0
#         self._ready_to_place = self._time_required == 0.0 and self.wafer_count < self.capacity

#         return self._time_required

#     @overrides
#     def take_out_wafer(self) -> Wafer:
#         """Returns none if has no wafer to return"""
#         if self.wafer_count == 0:
#             return None
#         w = self._wafer_qu.pop()
#         assert w != None
#         if len(self._wafer_qu) == 0:
#             self._curr_waypoint_no = 0
#         self._wafer_count = len(self._wafer_qu)
#         self.time_elapsed(0)  # update status
#         return w

#     @overrides
#     def top_wafer(self) -> Wafer:
#         """Returns none if has no wafer to return"""
#         if self.wafer_count == 0:
#             return None
#         w = self._wafer_qu[-1]
#         return w

#     @overrides
#     def put_in_wafer(self, wafer: Wafer):
#         assert wafer != None
#         wafer.waypoint += 1
#         self._wafer_qu.append(wafer)
#         assert wafer.waypoint in self._waypoint_list
#         self._wafer_count = len(self._wafer_qu)
#         self._curr_waypoint_no = self.top_wafer().waypoint  # top wafer waypoint
#         self.time_elapsed(0)  # update status

#     @overrides
#     def to_string(self, prefix=""):
#         wafers = "\n".join([wafer.to_string(prefix=prefix + "    ") for wafer in self._wafer_qu])
#         s = f"{prefix}ID={self.ID}, Name={self.Name}, time_required={self._time_required}, ready_to_pick={self._ready_to_pick}, ready_to_place={self._ready_to_place}\n    {prefix}Wafers={wafers}"
#         return s


class SimLoadPort(SimUnit):

    def __init__(self, id: int, name: str, unit_type: str, process_timespan: float, pos: pos3d):
        super().__init__(id=id, name=name, unit_type=unit_type, process_timespan=process_timespan, pos=pos)

        self.before_process = 0
        self.after_process = 0
        self.initial_unprocessed_wafer_count = S_SimConfInst.wafer_count
        self.slots: list[Wafer] = list()

    def generate_wafer(self):
        for i in range(1, self.initial_unprocessed_wafer_count + 1):
            self.slots.append(Wafer(id=i, waypoint=self._waypoint_list[0]))
            self.before_process += 1

    @property
    def is_full(self) -> bool:
        return self.before_process + self.after_process == self.initial_unprocessed_wafer_count

    @overrides
    def get_wafer_gen(self) -> Generator[Wafer, None, None]:
        for wafer in self.slots:
            if wafer != None and wafer.done == False:
                yield wafer

    def reset(self):
        SimUnit.reset(self)
        self.before_process = 0
        self.after_process = 0
        self.slots.clear()

        self.generate_wafer()
        # self._wafer_count = self.before_process

    @overrides
    def time_elapsed(self, timestep) -> float:

        self._time_required -= timestep
        self._time_required = max(self._time_required, 0.0)
        self._pending_time = 0
        has_undone_wafer = False
        all_slots_occupied = True

        if self.before_process != 0:
            has_undone_wafer = True
        if self.before_process + self.after_process < self.initial_unprocessed_wafer_count:
            all_slots_occupied = False

        if timestep > 0:
            for wafer in self.slots:
                if wafer != None and wafer.done == False:
                    wafer.record_trajectory(self.Name, timestep)

        self._ready_to_pick = has_undone_wafer
        self._ready_to_place = all_slots_occupied == False
        if has_undone_wafer:
            self._curr_waypoint_no = self._waypoint_list[0]
            self._wafer_id = self.top_wafer().id
        else:
            self._curr_waypoint_no = 0
            self._wafer_id = 0
        return self._time_required

    @overrides
    def take_out_wafer(self) -> Wafer:
        """Returns none if has no wafer to return"""

        if self.before_process == 0:
            return None
        wafer: Wafer = self.slots[self.initial_unprocessed_wafer_count - self.before_process]
        assert wafer != None, f"load port empty slot"
        # assert len(wafer.trajectory) == 0, f"Cannot take out after processing."
        self.slots[self.initial_unprocessed_wafer_count - self.before_process] = None
        self.before_process -= 1
        # self._wafer_count -= 1
        self.time_elapsed(0)  # update status
        return wafer

    @overrides
    def top_wafer(self) -> Wafer:
        if self.before_process == 0:
            return None
        wafer: Wafer = self.slots[self.initial_unprocessed_wafer_count - self.before_process]
        return wafer

    @overrides
    def put_in_wafer(self, wafer: Wafer):
        assert wafer != None
        self.slots[wafer.id - 1] = wafer
        self.after_process += 1
        wafer.done = True
        wafer.waypoint = -1  # done
        self.time_elapsed(0)  # update status

    @overrides
    def to_string(self, prefix=""):
        lst = [prefix + f"LoadPort:"]
        for wafer in self.slots:
            if wafer != None:
                lst.append(wafer.to_string(prefix))
        return f"\n{prefix}".join(lst)


#####################################
##
## SimTransport
##
class SimTransport(TransportInfo, ITimeElapsable):
    """A device capable of moving a wafer. Multiple arms are attached to one transport."""

    def __init__(
        self,
        id: int,
        name: str,
        arm_count: int,
        pos: pos3d,
        velocity: int,
    ):
        super().__init__(arm_count, pos=pos)
        self._id: int = id
        self._name: str = name
        self._velocity: int = velocity
        self._has_wafer_flag = False
        self._wafers: list[Wafer] = [None] * arm_count
        self._ori_pos = copy.deepcopy(pos)

        self._idle_move_flag = False  # it is to check whether it acts reduntant move(e.g. move twice)
        self._idle_move_action = SingleAction()
        self._bl_last_pick_or_place = 0  # 0=none, 1=pick, 2=place
        self._bl_last_waypoint = 0
        self.last_pnp_action: SingleAction = SingleAction()

    def is_full_if_pick(self, arm_index: int):
        for i in self._curr_waypoint:
            if i == arm_index:
                continue
            if i == 0:
                return False
        return True

    @property
    def ID(self):
        return self._id

    @property
    def Name(self):
        return self._name

    @property
    def has_wafer(self) -> bool:
        return self._has_wafer_flag

    @property
    def busy(self) -> bool:
        return self._time_required != 0

    def reset(self):
        self._time_required = 0
        self._curr_pos = copy.deepcopy(self._ori_pos)
        self._curr_action._target_pos.set_empty()
        self._curr_waypoint = [0] * self._arm_count

        self._curr_action.reset()
        self._bl_last_pick_or_place = 0
        self._bl_last_waypoint = 0
        self._has_wafer_flag = False
        self._wafers: list[Wafer] = [None] * self._arm_count

    def get_wafer(self, arm_index) -> Wafer:
        return self._wafers[arm_index - 1]

    def get_wafer_gen(self) -> Generator[Wafer, None, None]:
        for wafer in self._wafers:
            if wafer != None:
                yield wafer

    def ready_to_pick(self, arm_index) -> bool:
        return self._ready_to_pick[arm_index - 1]

    def ready_to_place(self, arm_index) -> bool:
        return self._ready_to_place[arm_index - 1]

    # implementation of abstract
    def time_elapsed(self, elapsed_time) -> int:
        """After some time has passed, modify the timestep and location information."""

        if elapsed_time > 0:
            self._action_set_flag = False
        self._time_required -= elapsed_time
        self._time_required = max(self._time_required, 0.0)
        prev_pos = copy.deepcopy(self._curr_pos)
        # Write the time spent in wafer's trajectory.
        for i, wafer in enumerate(self._wafers):
            if wafer != None:
                wafer.record_trajectory(f"{self.Name}.{i+1}", elapsed_time)

        # ARRIVED!
        if self._time_required == 0.0 and self._curr_action._target_pos.empty == False:

            target_unit: SimUnit = self._curr_action._tag

            # PICK
            if self._curr_action.command == CommandType.pick:
                wafer = target_unit.take_out_wafer()
                self.receive_wafer(arm_index=self._curr_action.arm_index, wafer=wafer, update_status=False)
                self.last_pnp_action.copy_from(self._curr_action)

            # PLACE
            elif self._curr_action.command == CommandType.place:
                aidx = self._curr_action.arm_index
                assert target_unit.check_waypoint_to_place(self._curr_waypoint[aidx - 1])
                wafer = self.hand_over_wafer(arm_index=aidx, update_status=False)
                target_unit.put_in_wafer(wafer)
                self.last_pnp_action.copy_from(self._curr_action)

            self._curr_pos.update_position(self._curr_action._target_pos)
            self._curr_action._target_pos.set_empty()
            self._curr_action.reset()

        # On Moving!
        elif self._curr_action._target_pos.empty == False:
            # Update current position based on velocity.
            self._curr_pos.update_position(
                utils.calc_pos_by_time(self._curr_pos, self._curr_action._target_pos, self._velocity, elapsed_time)
            )

        wafer_exists = False
        for i, wafer in enumerate(self._wafers):
            self._ready_to_pick[i] = self._time_required == 0.0 and wafer == None
            self._ready_to_place[i] = self._time_required == 0.0 and wafer != None
            if wafer != None:
                wafer_exists = True

        self._has_wafer_flag = wafer_exists

        moving_dist = utils.get_distance(prev_pos, self._curr_pos)
        return moving_dist

    def hand_over_wafer(self, arm_index, update_status=True) -> Wafer:
        """return Wafer, waypoint_number"""
        assert self._wafers[arm_index - 1] != None
        w = self._wafers[arm_index - 1]
        self._wafers[arm_index - 1] = None
        self._curr_waypoint[arm_index - 1] = 0
        self._bl_last_waypoint = w.waypoint
        self._curr_wafer_id[arm_index - 1] = 0
        if update_status:
            self.time_elapsed(0)  # update status
        return w

    def receive_wafer(self, arm_index, wafer: Wafer, update_status=True):
        assert self._wafers[arm_index - 1] == None, "wafer exists"
        self._wafers[arm_index - 1] = wafer
        self._curr_waypoint[arm_index - 1] = wafer.waypoint
        self._bl_last_waypoint = wafer.waypoint
        self._curr_wafer_id[arm_index - 1] = wafer.id
        if update_status:
            self.time_elapsed(0)  # update status

    def calc_transport_timestep(self) -> int:
        """Calculate the expected timestep based on distance and speed to the target point."""
        assert self._curr_action._target_pos.empty == False
        sec = utils.calc_move_time_sec(self._curr_pos, self._curr_action._target_pos, self._velocity)
        # sec = math.ceil(sec)
        return sec

    def set_action(self, state: EQState, action: SingleAction) -> ActionResult:
        """return : action reward"""
        if self._action_set_flag:
            return ActionResult.invalid_action

        result = ActionResult.ok
        self._action_set_flag = True
        if action.command == CommandType.no_op:
            pass

        elif action.command == CommandType.move:
            self._curr_action.copy_from(action)
            self._curr_action._tag = None

            unit = state.get_unit(action.target_index)
            assert unit != None
            self._curr_action._tag = unit
            self._curr_action._target_pos.update_position(unit.position)
            self._time_required = self.calc_transport_timestep()

            # move twice penalty. (idle move)
            if self._idle_move_flag and self._idle_move_action.target_name != action.target_name:
                result = ActionResult.idle_move

            self._idle_move_flag = True  # set flag on for checking the next action
            self._idle_move_action.copy_from(action)  # remeber last 'move' command

        else:  # case: pick and place

            self._bl_last_pick_or_place = 1 if action.command is CommandType.pick else 2
            self._curr_action.copy_from(action)
            self._curr_action._tag = None
            unit: SimUnit = state.get_unit(action.target_index)
            assert unit != None
            if action.command == CommandType.pick:
                assert unit.ready_to_pick
            if action.command == CommandType.place:
                assert unit.ready_to_place
            self._curr_action._tag = unit
            self._curr_action._target_pos.update_position(unit.position)
            self._time_required = self.calc_transport_timestep() + S_SimConfInst.pick_and_place_time

            if self._idle_move_flag:
                if self._idle_move_action.target_name != action.target_name:
                    result = ActionResult.idle_move
                # hit the move prediction!
                if self._curr_pos.is_equal(unit.position):
                    result = ActionResult.hit_the_move

            self._idle_move_flag = False  # reset flag
            self._idle_move_action.reset()

        self.time_elapsed(0)  # update status
        return result

    def to_string(self, prefix=""):
        t = []
        for w in self._wafers:
            t.append("None" if w == None else "Exists")

        s = f"{prefix}{self.Name}[{self.ID}], rqtime:{self._time_required}, curr_act:<{self._curr_action.to_string()}>, wp:{self._curr_waypoint}, r2place:{self._ready_to_place}, r2pick:{self._ready_to_pick} wf:{t}"
        return s
