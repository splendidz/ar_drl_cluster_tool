import torch
from error_code import ErrorCode
from s_action_mgr import CommandType, S_ActionMgrInst
from sim_classes import SimTransport, SimUnit
from typing import Dict, Tuple, List
from s_simulator_config import S_SimConfInst
from state_tensors import EQState
import tensor_field_map as MAP
import numpy as np


class DeadlockState:
    def __init__(self, unit_indices: List[int], transport_and_arm: List[Tuple], waypoints: List[int]):
        self.unit_indices: List[int] = unit_indices
        self.transport_and_arm: List[Tuple] = transport_and_arm  # tuple(transport id, arm index)
        self.waypoints: List[int] = waypoints


class S_ActionValidator:  # singleton

    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_ActionValidator()
        return cls._instance

    def __init__(self):
        self.deadlock_state_list: List[DeadlockState] = []
        self.related_transports: List[List[DeadlockState]] = None
        self.RELEVANT_STATE_MASK = np.ndarray(shape=(0,))
        self.action_mask_repos: Dict[str, torch.Tensor] = {}
        self.all_action_list = []
        self._initialized = False
        self.locked = False

    def initialize(self, action_count):
        if self._initialized == True:
            return
        self._initialized = True

        for i_action in range(action_count):
            self.all_action_list.append(i_action)

    def set_transport_count(self, tr_count):
        if self.locked == False:
            self.related_transports = [[] for _ in range(tr_count + 1)]

    def add_deadlock_state(self, deadlock: DeadlockState) -> bool:
        if self.locked == True:
            return False

        for tu in deadlock.transport_and_arm:
            tr_id = tu[0]
            if deadlock not in self.related_transports[tr_id]:
                self.related_transports[tr_id].append(deadlock)

        self.deadlock_state_list.append(deadlock)
        return True

    def lock(self):
        self.locked = True

    def GET_RELEVANT_STATE_MASK(self, shape) -> np.ndarray:
        """Make relevant action mask array. It's the range of interests of the state array."""
        # Initialize the mask with ones
        mask = np.ones(shape, dtype=float)

        # Offset for iterating through unit and transport sections
        offset = 0

        # Handle unit data masking
        for _ in range(S_SimConfInst.unit_max_padding):
            mask[offset + MAP.UNIT.REQUIRED_TIMESTEP] = 0.0
            mask[offset + MAP.UNIT.WAFER_ID] = 0.0
            mask[offset + MAP.UNIT.POS_X] = 0.0
            mask[offset + MAP.UNIT.POS_Y] = 0.0
            mask[offset + MAP.UNIT.POS_Z] = 0.0
            offset += MAP.UNIT.LENGTH

        # Handle transport data masking
        for _ in range(S_SimConfInst.transport_max_padding):
            mask[offset + MAP.TRANSPORT.REQUIRED_TIMESTEP] = 0.0
            mask[offset + MAP.TRANSPORT.CURRENT_POS_X] = 0.0
            mask[offset + MAP.TRANSPORT.CURRENT_POS_Y] = 0.0
            mask[offset + MAP.TRANSPORT.CURRENT_POS_Z] = 0.0
            mask[offset + MAP.TRANSPORT.CMD_TARGET_POS_X] = 0.0
            mask[offset + MAP.TRANSPORT.CMD_TARGET_POS_Y] = 0.0
            mask[offset + MAP.TRANSPORT.CMD_TARGET_POS_Z] = 0.0
            mask[offset + MAP.TRANSPORT.WAFER_ID_ARM1] = 0.0
            mask[offset + MAP.TRANSPORT.WAFER_ID_ARM2] = 0.0
            offset += MAP.TRANSPORT.LENGTH

        mask[offset + MAP.GLOBAL.TIME_STEP] = 0.0
        return mask

    def convert_state_to_tuple(self, state_array: np.ndarray) -> Tuple:

        if len(self.RELEVANT_STATE_MASK) == 0:  # make once
            self.RELEVANT_STATE_MASK = self.GET_RELEVANT_STATE_MASK(state_array.shape)

        # make simplifed state. the states are used as dictionary key.
        # to get action mask from simplified state
        masked_state = state_array * self.RELEVANT_STATE_MASK
        # state_tuple = tuple(round(x, 6) for x in masked_state.tolist())  # Round each value
        state_tuple = tuple(masked_state.tolist())
        return state_tuple

    def find_action_mask_from_repos(self, state_array: np.ndarray) -> np.ndarray:

        key = self.convert_state_to_tuple(state_array)
        action_mask = self.action_mask_repos.get(key)
        return action_mask

    def add_action_mask_to_repos(self, state_array: np.ndarray, action_mask: np.ndarray):

        key = self.convert_state_to_tuple(state_array)
        if len(self.action_mask_repos) == 100000:
            self.action_mask_repos.popitem()
        prev_mask = self.action_mask_repos.get(key)
        if prev_mask is not None:
            if np.array_equal(prev_mask, action_mask) == False:
                print(f"prev mask: \n\t{prev_mask}")
                print(f"\ncurr mask: \n\t{action_mask}")
                print(f"\ndiff{action_mask == prev_mask}")
                assert False

        self.action_mask_repos[key] = action_mask

    def get_action_mask(self, state_array: np.ndarray, state_obj) -> np.ndarray:

        use_mask_repos = False  # 버그 존재. action mask 달라짐

        if use_mask_repos:
            if state_array is None:
                state_array = state_obj.to_array()
            action_mask: np.ndarray = self.find_action_mask_from_repos(state_array)
            if action_mask is not None:
                return action_mask

        # Shape: (tid, action_count)
        action_mask = np.zeros(len(self.all_action_list), dtype=float)
        for i_action in self.all_action_list:
            err_code = self.check_action(state_obj, i_action)
            if err_code == ErrorCode.ok:
                action_mask[i_action] = 1.0

        if use_mask_repos:
            self.add_action_mask_to_repos(state_array, action_mask)
        return action_mask

    def check_deadlock(self, state: EQState, transport_id_to_pick, arm_index_to_pick, target_waypoint: int) -> bool:
        """call this function when pick a wafer
        returns True when it's not deadlock state. False when the action will cause deadlock.
        """

        if len(self.related_transports[transport_id_to_pick]) == 0:
            return True

        results = []
        for deadlock_state in self.related_transports[transport_id_to_pick]:
            deadlock_state: DeadlockState = deadlock_state
            units_full = True
            for uid in deadlock_state.unit_indices:
                unit: SimUnit = state.get_unit(uid)
                if unit.is_full == False:
                    units_full = False
                    break
            arms_full = True
            for tu in deadlock_state.transport_and_arm:
                tid = tu[0]
                arm_id = tu[1]
                transport: SimTransport = state.get_transport(tid)
                if arm_id == arm_index_to_pick:
                    continue
                if transport.get_wafer(arm_id) == None:
                    arms_full = False
                    break
            waypoint_okay = True
            if target_waypoint in deadlock_state.waypoints:
                waypoint_okay = False

            results.append(units_full == False or arms_full == False or waypoint_okay == True)

        b = all(results)
        if b == False and target_waypoint == 1:
            b = b  ##%!
        return b
        # return False  # false means it's deadlock

    def check_action(self, state_obj: EQState, i_action: int) -> ErrorCode:

        action = S_ActionMgrInst.get_action(i_action, do_copy=False)
        # if action.tr_index != target_tid:
        #     return ErrorCode.action_ownership_error

        tr: SimTransport = state_obj.get_transport(action.tr_index)
        if tr._action_set_flag:
            return ErrorCode.already_set_action

        if S_SimConfInst.use_sequential_action_selection:
            if tr.ID != state_obj.current_action_tr_idx:
                return ErrorCode.unsequential_action_turn

        if action.command == CommandType.no_op:
            ## if tr._last_set_action_timestep == current_timestep:
            ##     return ErrorCode.already_set_action
            ## else:
            return ErrorCode.ok

        unit: SimUnit = state_obj.get_unit(action.target_index)

        if tr.busy == True:
            return ErrorCode.busy_transport

        # pair action mode
        if S_SimConfInst.enable_pair_action and tr.wafer_count == 1:
            if tr.last_pnp_action.command != action.command:
                return ErrorCode.pair_action_needed

        if action.command == CommandType.move:
            return ErrorCode.ok

        elif action.command == CommandType.pick:
            if unit.busy == True:
                return ErrorCode.busy_unit

            if tr.ready_to_pick(action.arm_index) == False:
                return ErrorCode.occupied_transport

            if unit.ready_to_pick == False:
                return ErrorCode.empty_unit

            wafer = unit.top_wafer()
            if self.check_deadlock(state_obj, action.tr_index, action.arm_index, wafer.waypoint) == False:
                return ErrorCode.deadlock

        elif action.command == CommandType.place:

            if unit.busy == True:
                return ErrorCode.busy_unit

            if tr.ready_to_place(action.arm_index) == False:
                return ErrorCode.empty_transport

            if unit.ready_to_place == False:
                return ErrorCode.occupied_unit

            if unit.check_waypoint_to_place(tr._curr_waypoint[action.arm_index - 1]) == False:
                return ErrorCode.non_sequencial_waypoint

        return ErrorCode.ok


S_ActionValidatorInst = S_ActionValidator.inst()
"""

def check_action_validation2(observation_state: torch.Tensor, i_action: int) -> ErrorCode:

    action = ActionMgr.inst().get_action(i_action)

    if action.command == CommandType.no_op:
        return ErrorCode.ok

    offset = 0
    unit_tensor_list = list()
    transport_tensor_list = list()
    target_tensor_index = action.target_index - 1
    if True:  # ORIGINAL CODE
        for i in range(GlobalValues.unit_max_padding):
            unit_tensor_list.append(observation_state[offset : offset + TensorFieldMap_Unit.LENGTH])
            offset += TensorFieldMap_Unit.LENGTH

        for i in range(GlobalValues.transport_max_padding):
            transport_tensor_list.append(observation_state[offset : offset + TensorFieldMap_Transport.LENGTH])
            offset += TensorFieldMap_Transport.LENGTH

        tr_tensor = transport_tensor_list[action.tr_index]
        target_unit_tensor = unit_tensor_list[target_tensor_index]

    if True:
        # Calculate offsets for the requested tensors directly
        unit_offset = target_tensor_index * TensorFieldMap_Unit.LENGTH
        transport_offset = (
            GlobalValues.unit_max_padding * TensorFieldMap_Unit.LENGTH
            + action.tr_index * TensorFieldMap_Transport.LENGTH()
        )

        # Extract the target unit tensor
        target_unit_tensor = observation_state[unit_offset : unit_offset + TensorFieldMap_Unit.LENGTH]

        # Extract the transport tensor
        tr_tensor = observation_state[transport_offset : transport_offset + TensorFieldMap_Transport.LENGTH()]
        tr_arm_index_pos = TensorFieldMap_Transport.ArmCurrWayPointStart + action.arm_index - 1

    if tr_tensor[TensorFieldMap_Transport.Timestep] != 0:
        return ErrorCode.busy_transport

    if action.command == CommandType.move:
        return ErrorCode.ok

    elif action.command == CommandType.pick:
        if target_unit_tensor[TensorFieldMap_Unit.TimeStep] != 0:
            return ErrorCode.busy_unit

        if tr_tensor[tr_arm_index_pos] != 0:
            return ErrorCode.occupied_transport

        if target_unit_tensor[TensorFieldMap_Unit.ReadyToPick] == 0:
            return ErrorCode.empty_unit

        # if tr.check_pick_deadlock(action.arm_index) == False:
        #     return ErrorCode.deadlock

    elif action.command == CommandType.place:

        if target_unit_tensor[TensorFieldMap_Unit.TimeStep] != 0:
            return ErrorCode.busy_unit

        if tr_tensor[tr_arm_index_pos] == 0:
            return ErrorCode.empty_transport

        if target_unit_tensor[TensorFieldMap_Unit.ReadyToPlace] == 0:
            return ErrorCode.occupied_unit

        arm_wafer_waypoint = round(float(tr_tensor[tr_arm_index_pos]) * GlobalValues.max_waypoint)
        rslt = WaypointChecker.inst().check_waypoint_to_place_by_id(action.target_index, arm_wafer_waypoint)
        if rslt == False:
            return ErrorCode.non_sequencial_waypoint

    return ErrorCode.ok

"""
