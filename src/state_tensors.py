import torch
import torch.nn.functional as F
from utils import pos3d
from action_space import SingleAction
from utils import members_to_string
import copy
from s_simulator_config import S_SimConfInst
import numpy as np


#####################################
##
## UnitInfo
##
class UnitInfo:
    """Essential information for learning. This is the input to the encoder."""

    def __init__(self, pos: pos3d = pos3d.EmptyPos()):

        self._time_required: float = 0
        """ Time remaining time for the process. """
        self._curr_waypoint_no: int = 0
        """ Waypoint number of the current wafer is in progress."""
        self._ready_to_pick: bool = False
        """ The wafer exists and can be taken. """
        self._ready_to_place: bool = False
        """ A state where there is no wafer and another wafer can be received."""
        self._wafer_id: int = 0
        """ Wafer number that currently has."""
        # self._wafer_count: int = 0
        """ Current holding wafer count. """
        self._pos: pos3d = copy.deepcopy(pos)
        """ Location of the device."""

    @property
    def position(self):
        return self._pos

    def to_list(self) -> list:
        # Build a list to collect all data
        data = []

        data.append(self._time_required * S_SimConfInst._instance.max_process_time_reciprocal)
        data.append(self._curr_waypoint_no * S_SimConfInst._instance.max_waypoint_reciprocal)
        data.append(float(self._ready_to_pick))
        data.append(float(self._ready_to_place))
        data.append(self._wafer_id * S_SimConfInst._instance.MAX_WAFER_NO_RECIPROCAL)
        # data.append(self._wafer_count * SimConfInst._instance.MAX_WAFER_NO_RECIPROCAL)
        data.extend(self._pos.get_scaled_pos())

        return data

    def to_array(self) -> np.ndarray:
        # Build a NumPy array to collect all data
        data = np.array(
            [
                self._time_required * S_SimConfInst._instance.max_process_time_reciprocal,
                self._curr_waypoint_no * S_SimConfInst._instance.max_waypoint_reciprocal,
                float(self._ready_to_pick),
                float(self._ready_to_place),
                self._wafer_id * S_SimConfInst._instance.MAX_WAFER_NO_RECIPROCAL,
                # self._wafer_count * SimConfInst._instance.MAX_WAFER_NO_RECIPROCAL,
            ],
            dtype=float,
        )

        data = np.concatenate([data, self._pos.get_scaled_pos()])
        return data


#####################################
##
## TransportInfo
##
class TransportInfo:
    """Essential information for learning. This is the input to the encoder."""

    def __init__(self, arm_count: int, pos: pos3d = pos3d.EmptyPos()):

        self._action_set_flag = False
        self._time_required: float = 0
        """ Time remaining time for the tranfering."""
        self._curr_pos: pos3d = copy.deepcopy(pos)
        """ Transport position."""
        self._ready_to_pick: list[int] = [0] * arm_count
        self._ready_to_place: list[int] = [0] * arm_count

        self._curr_waypoint: list[int] = [0] * arm_count
        """Waypoint each arms."""
        self._curr_wafer_id: list[int] = [0] * arm_count
        self._arm_count = arm_count

        self._curr_action = SingleAction()

        self.relevant_unit_indices: list[int] = []

    @property
    def has_wafer(self) -> bool:
        for w in self._curr_waypoint:
            if w != 0:
                return True

        return False

    @property
    def wafer_count(self) -> int:
        cnt = 0
        for w in self._curr_waypoint:
            if w != 0:
                cnt += 1
        return cnt

    def to_array(self) -> np.ndarray:
        action_set_flag = np.array([self._action_set_flag], dtype=float)
        time_required = np.array([self._time_required * S_SimConfInst._instance.max_process_time_reciprocal], dtype=float)
        curr_action = np.array(self._curr_action.to_array(), dtype=float)
        curr_pos = np.array(self._curr_pos.get_scaled_pos(), dtype=float)
        ready_to_pick = np.array(self._ready_to_pick, dtype=float)
        ready_to_place = np.array(self._ready_to_place, dtype=float)
        curr_waypoint = np.array(self._curr_waypoint, dtype=float) * S_SimConfInst._instance.max_waypoint_reciprocal
        curr_wafer_id = np.array(self._curr_wafer_id, dtype=float) * S_SimConfInst._instance.MAX_WAFER_NO_RECIPROCAL

        # Determine padding if necessary
        num_arms = len(self._curr_waypoint)
        pad_cnt = S_SimConfInst._instance.max_arm_count - num_arms
        if pad_cnt > 0:
            padding = np.zeros(pad_cnt, dtype=float)
        else:
            padding = np.array([], dtype=float)

        # Apply padding where necessary
        ready_to_pick_padded = np.concatenate([ready_to_pick, padding]) if pad_cnt > 0 else ready_to_pick
        ready_to_place_padded = np.concatenate([ready_to_place, padding]) if pad_cnt > 0 else ready_to_place
        curr_waypoint_padded = np.concatenate([curr_waypoint, padding]) if pad_cnt > 0 else curr_waypoint
        curr_wafer_id_padded = np.concatenate([curr_wafer_id, padding]) if pad_cnt > 0 else curr_wafer_id

        data = np.concatenate(
            [
                action_set_flag,
                time_required,
                curr_action,
                curr_pos,
                ready_to_pick_padded,
                ready_to_place_padded,
                curr_waypoint_padded,
                curr_wafer_id_padded,
            ]
        )

        return data


#####################################
##
## EQState
##
class EQState:

    def __init__(self, unit_list: list[UnitInfo], transport_list: list[TransportInfo]):
        self._unit_list = unit_list
        self._transport_list = transport_list
        self.current_timestep = 0
        self.current_action_tr_idx = 1  # tr start index

    # @property
    # def pending_wafer_count(self):
    #     """unprocessed wafer count in the equipement"""
    #     cnt = 0
    #     for u in self._unit_list:
    #         cnt += u.
    #     for t in self._transport_list:
    #         cnt += t.wafer_count
    #     return cnt

    @property
    def unit_count(self) -> int:
        return len(self._unit_list)

    @property
    def transport_count(self) -> int:
        return len(self._transport_list)

    def get_unit(self, id) -> UnitInfo:
        return self._unit_list[id - 1]

    def get_transport(self, id) -> TransportInfo:
        return self._transport_list[id - 1]

    def set_timestep(self, ts):
        # set as timestep delta
        self.current_timestep = ts - self.current_timestep

    def reset(self):
        for unit in self._unit_list:
            unit.reset()  # child class reset function
        for tr in self._transport_list:
            tr.reset()  # child class reset function
        self.current_timestep = 0
        self.current_action_tr_idx = 1  # tr start index

    def is_done(self):
        for unit in self._unit_list:
            if unit._ready_to_pick == True or unit._curr_waypoint_no != 0 or unit._time_required != 0:
                return False
        for transport in self._transport_list:
            if transport.has_wafer:
                return False
        return True

    def get_observation_state(self) -> np.ndarray:
        return self.to_array()

    def to_array(self, round_at=4) -> np.ndarray:
        """[All Units] + [All Transports]"""
        # Process unit data
        unit_data = np.array([unit.to_array() for unit in self._unit_list], dtype=float)

        # Padding logic for unit_list
        num_units = unit_data.shape[0]
        unit_padding = S_SimConfInst.unit_max_padding - num_units
        if unit_padding > 0:
            pad_data = np.zeros((unit_padding, unit_data.shape[1]), dtype=float)
            unit_data = np.vstack([unit_data, pad_data])

        # Process transport data
        transport_data = np.array([transport.to_array() for transport in self._transport_list], dtype=float)

        # Padding logic for transport_robot_list
        num_transports = transport_data.shape[0]
        transport_padding = S_SimConfInst.transport_max_padding - num_transports
        if transport_padding > 0:
            pad_data = np.zeros((transport_padding, transport_data.shape[1]), dtype=float)
            transport_data = np.vstack([transport_data, pad_data])

        timestep = np.array([round(self.current_timestep / 10, 2)], dtype=float)
        # Combine unit_data and transport_data into a single array
        combined_data = np.concatenate([unit_data.flatten(), transport_data.flatten(), timestep])

        if round == 0:
            return combined_data
        else:
            return combined_data.round(round_at)

    def to_array_v2(self) -> np.ndarray:
        """[ Transport Info + All units and masking uninvolved units ] * n Transports"""
        # Process unit data
        unit_data = np.array([unit.to_array() for unit in self._unit_list], dtype=float)

        # Padding logic for unit_list
        num_units = unit_data.shape[0]
        unit_padding = S_SimConfInst.unit_max_padding - num_units
        if unit_padding > 0:
            pad_data = np.zeros((unit_padding, unit_data.shape[1]), dtype=float)
            unit_data = np.vstack([unit_data, pad_data])

        # Process transport data
        transport_data = np.array([transport.to_array() for transport in self._transport_list], dtype=float)

        # Padding logic for transport_robot_list
        num_transports = transport_data.shape[0]
        transport_padding = S_SimConfInst.transport_max_padding - num_transports
        if transport_padding > 0:
            pad_data = np.zeros((transport_padding, transport_data.shape[1]), dtype=float)
            transport_data = np.vstack([transport_data, pad_data])

        # Combine data in the requested order
        combined_data = []
        for transport, transport_row in zip(self._transport_list, transport_data):
            combined_data.append(transport_row)  # Add transport_data

            # Prepare unit data based on relevant_unit_indices
            relevant_unit_data = np.zeros_like(unit_data)  # Initialize with zeros
            for idx in transport.relevant_unit_indices:
                relevant_unit_data[idx] = unit_data[idx]  # Add only relevant units

            combined_data.extend(relevant_unit_data)  # Add relevant unit_data

        flattened_data = []
        for item in combined_data:
            if isinstance(item, (np.ndarray, list)):
                flattened_data.extend(np.ravel(item))  # Flatten and append
            else:
                flattened_data.append(item)  # Append scalars directly

        # Convert the flattened list to a NumPy array
        combined_data = np.array(flattened_data, dtype=float)

        return combined_data

    def to_string(self, prefix=""):

        s = []
        s.append("> Units")
        for h in self._unit_list:
            s.append(h.to_string("   "))

        s.append("> Transports")
        for dev in self._transport_list:
            s.append(dev.to_string("   "))

        return f"\n{prefix}".join(s)
