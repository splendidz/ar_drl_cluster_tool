from typing import Tuple, Dict, List
from state_tensors import EQState
from sim_classes import SimTransport, SimUnit
from action_space import CommandType, SingleAction
from s_action_mgr import S_ActionMgrInst
from s_action_validator import S_ActionValidatorInst
import numpy as np
import utils
from collections import defaultdict
import random


def find_ready_to_pick_in_group(group_name: str, unit_dict: Dict[str, SimUnit]) -> SimUnit:
    grp: List[SimUnit] = [unit for unit in unit_dict.values() if unit.Name.find(group_name) == 0 and unit.ready_to_pick]
    assert len(grp) > 0
    min_wafer_id = float("inf")
    min_id_unit = grp[0]
    for unit in grp:
        if min_wafer_id > unit._wafer_id:
            min_wafer_id = unit._wafer_id
            min_id_unit = unit
    return min_id_unit


def get_ready_to_pick_count(group_name: str, unit_dict: Dict[str, SimUnit]) -> SimUnit:
    grp: List[SimUnit] = [unit for unit in unit_dict.values() if unit.Name.find(group_name) == 0 and unit.ready_to_pick]
    return len(grp)


def find_ready_to_place_in_group(group_name: str, unit_dict: Dict[str, SimUnit]) -> SimUnit:
    grp: List[SimUnit] = [unit for unit in unit_dict.values() if unit.Name.find(group_name) == 0 and unit.ready_to_place]
    assert len(grp) > 0
    return grp[0]


def get_ready_to_place_count(group_name: str, unit_dict: Dict[str, SimUnit]) -> SimUnit:
    grp: List[SimUnit] = [unit for unit in unit_dict.values() if unit.Name.find(group_name) == 0 and unit.ready_to_place]
    return len(grp)


class Greedy:

    def __init__(self):
        self.unit_dict: Dict[str, SimUnit] = {}
        self.transport_dict: Dict[str, SimTransport] = {}

    def make_once(self, state_obj: EQState):
        if len(self.unit_dict) != 0:
            return

        for unit in state_obj._unit_list:
            unit: SimUnit = unit
            self.unit_dict[unit.Name] = unit

        for tr in state_obj._transport_list:
            tr: SimTransport = tr
            self.transport_dict[tr.Name] = tr

    def do_TR1(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["TR1"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:

            wayno = transport.get_wafer(1).waypoint
            buf1_rd2pl_cnt = get_ready_to_place_count("Buffer1.", unit_dict)

            if wayno == 8:  # buffer2 -> LP
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name="LoadPort"
                )
            elif wayno == 1 and buf1_rd2pl_cnt >= 2:  # LoadPort -> Buffer1
                unit = find_ready_to_place_in_group("Buffer1.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 1:
            wayno = 0
            if transport.get_wafer(1) != None:
                wayno = transport.get_wafer(1).waypoint
            else:
                wayno = transport.get_wafer(2).waypoint

            last_command = transport.last_pnp_action.command
            action = no_op

            if wayno == 1:  # LP
                if last_command == CommandType.pick:
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name="LoadPort"
                    )
                elif last_command == CommandType.place:
                    unit = find_ready_to_place_in_group("Buffer1.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            if wayno == 8:  # Buffer2
                if last_command == CommandType.pick:
                    unit = find_ready_to_pick_in_group("Buffer2.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_command == CommandType.place:
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name="LoadPort"
                    )

            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:

            loadport_has_wafer = get_ready_to_pick_count("LoadPort", unit_dict) > 0
            buf2_rd2pk_cnt = get_ready_to_pick_count("Buffer2.", unit_dict)
            buf1_rd2pl_cnt = get_ready_to_place_count("Buffer1.", unit_dict)

            action = no_op
            if loadport_has_wafer and buf1_rd2pl_cnt >= 2:
                # loadport pick
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name="LoadPort"
                )
            elif buf2_rd2pk_cnt >= 2:
                # buffer2 pick
                unit = find_ready_to_pick_in_group("Buffer2.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

    def do_TR2(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["TR2"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:
            wayno = transport.get_wafer(1).waypoint
            buf1_rd2pick_cnt = get_ready_to_pick_count("Buffer1.", unit_dict)
            unitA_rd2pl_cnt = get_ready_to_place_count("UnitA.", unit_dict)
            unitB_rd2pl_cnt = get_ready_to_place_count("UnitB.", unit_dict)
            buffer3_rd2pl_cnt = get_ready_to_place_count("Buffer3.", unit_dict)
            buffer2_rd2pl_cnt = get_ready_to_place_count("Buffer4.", unit_dict)

            if wayno == 2 and unitA_rd2pl_cnt >= 2:  # buffer1 -> unitA
                unit = find_ready_to_place_in_group("UnitA.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                )
            elif wayno == 3 and unitB_rd2pl_cnt >= 2:  # UnitA -> UnitB
                unit = find_ready_to_place_in_group("UnitB.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                )
            elif wayno == 4 and buffer3_rd2pl_cnt >= 2:  # UnitB -> Buffer3
                unit = find_ready_to_place_in_group("Buffer3.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                )
            elif wayno == 7 and buffer2_rd2pl_cnt >= 2:  # Buffer4 -> Buffer2
                unit = find_ready_to_place_in_group("Buffer2.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 1:

            wayno = 0
            if transport.get_wafer(1) != None:
                wayno = transport.get_wafer(1).waypoint
            else:
                wayno = transport.get_wafer(2).waypoint

            last_command = transport.last_pnp_action.command
            action = no_op
            if wayno == 2:  # buffer1

                if last_command == CommandType.pick:
                    unit = find_ready_to_pick_in_group("Buffer1.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_command == CommandType.place:
                    unit = find_ready_to_place_in_group("UnitA.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            elif wayno == 3:  # unit A

                if last_command == CommandType.pick:
                    unit = find_ready_to_pick_in_group("UnitA.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_command == CommandType.place:
                    unit = find_ready_to_place_in_group("UnitB.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            elif wayno == 4:  # unit B

                if last_command == CommandType.pick:
                    unit = find_ready_to_pick_in_group("UnitB.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_command == CommandType.place:
                    unit = find_ready_to_place_in_group("Buffer3.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            elif wayno == 7:  # buffer4

                if last_command == CommandType.pick:
                    unit = find_ready_to_pick_in_group("Buffer4.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_command == CommandType.place:
                    unit = find_ready_to_place_in_group("Buffer2.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            buf1_rd2pick_cnt = get_ready_to_pick_count("Buffer1.", unit_dict)
            buf2_rd2pl_cnt = get_ready_to_place_count("Buffer2.", unit_dict)
            buf4_rd2pk_cnt = get_ready_to_pick_count("Buffer4.", unit_dict)
            unitA_rd2pl_cnt = get_ready_to_place_count("UnitA.", unit_dict)
            unitA_rd2pk_cnt = get_ready_to_pick_count("UnitA.", unit_dict)
            unitB_rd2pl_cnt = get_ready_to_place_count("UnitB.", unit_dict)
            unitB_rd2pk_cnt = get_ready_to_pick_count("UnitB.", unit_dict)
            buf3_rd2pl_cnt = get_ready_to_place_count("Buffer3.", unit_dict)

            action = no_op
            if buf1_rd2pick_cnt >= 2 and unitA_rd2pl_cnt == 2:
                # buffer1 -> unit A
                unit = find_ready_to_pick_in_group("Buffer1.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif unitA_rd2pk_cnt == 2 and unitB_rd2pl_cnt >= 2:
                # unit A -> unit B
                unit = find_ready_to_pick_in_group("UnitA.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif unitB_rd2pk_cnt >= 2 and buf3_rd2pl_cnt >= 2:
                # unitB -> buf3
                unit = find_ready_to_pick_in_group("UnitB.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif buf4_rd2pk_cnt >= 2 and buf2_rd2pl_cnt >= 2:
                # buf4 -> buf2
                unit = find_ready_to_pick_in_group("Buffer4.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action
        return None

    def do_TR3(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["TR3"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        if transport.wafer_count == 2:

            unitC_rd2pl_cnt = get_ready_to_place_count("UnitC.", unit_dict)
            buffer4_rd2pl_cnt = get_ready_to_place_count("Buffer4.", unit_dict)
            action = no_op

            wafer_waypoint_no = transport.get_wafer(1).waypoint
            if wafer_waypoint_no == 5:  # buffer3
                if unitC_rd2pl_cnt >= 2:
                    unit = find_ready_to_place_in_group("UnitC.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                    )

            elif wafer_waypoint_no == 6:  # UnitC
                if buffer4_rd2pl_cnt >= 2:
                    unit = find_ready_to_place_in_group("Buffer4.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                    )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 1:

            wayno = 0
            if transport.get_wafer(1) != None:
                wayno = transport.get_wafer(1).waypoint
            else:
                wayno = transport.get_wafer(2).waypoint

            last_action_cmd = transport.last_pnp_action.command
            action = no_op
            if wayno == 5:  # Buffer3
                if last_action_cmd == CommandType.pick:
                    unit = find_ready_to_pick_in_group("Buffer3.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_action_cmd == CommandType.place:
                    unit = find_ready_to_place_in_group("UnitC.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            elif wayno == 6:  # UnitC
                if last_action_cmd == CommandType.pick:
                    unit = find_ready_to_pick_in_group("UnitC.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                    )
                elif last_action_cmd == CommandType.place:
                    unit = find_ready_to_place_in_group("Buffer4.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            buf3_rd2pk_cnt = get_ready_to_pick_count("Buffer3.", unit_dict)
            unitC_rd2pk_cnt = get_ready_to_pick_count("UnitC.", unit_dict)
            unitC_rd2pl_cnt = get_ready_to_place_count("UnitC.", unit_dict)
            buf4_rd2pl_cnt = get_ready_to_place_count("Buffer4.", unit_dict)

            action = no_op
            if buf4_rd2pl_cnt >= 2 and unitC_rd2pk_cnt >= 2:
                # unit C pick
                unit = find_ready_to_pick_in_group("UnitC.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif buf3_rd2pk_cnt >= 2 and unitC_rd2pl_cnt >= 2:
                # buffer3 pick
                unit = find_ready_to_pick_in_group("Buffer3.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

    def __call__(self, state_obj: EQState) -> SingleAction:

        self.make_once(state_obj)

        selected_action: SingleAction = None
        selected_action = self.do_TR1(self.transport_dict, self.unit_dict)
        if selected_action != None:
            return selected_action

        selected_action = self.do_TR2(self.transport_dict, self.unit_dict)
        if selected_action != None:
            return selected_action

        selected_action = self.do_TR3(self.transport_dict, self.unit_dict)
        if selected_action != None:
            return selected_action

        assert False, "No action to do."
