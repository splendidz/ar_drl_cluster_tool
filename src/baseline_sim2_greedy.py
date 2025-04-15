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

    def do_IDX(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["IDX"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:

            wayno = transport.get_wafer(1).waypoint
            ldbuf_rd2pl_cnt = get_ready_to_place_count("LDBuf.", unit_dict)

            if wayno == 10:  # UDBuf -> LP
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.place, target_name="LoadPort"
                )
            elif wayno == 1 and ldbuf_rd2pl_cnt >= 1:  # LoadPort -> Buffer1
                unit = find_ready_to_place_in_group("LDBuf.", unit_dict)
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
                    unit = find_ready_to_place_in_group("LDBuf.", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                    )

            if wayno == 10:  # UDBuf
                if last_command == CommandType.pick:
                    if get_ready_to_pick_count("UDBuf.", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("UDBuf.", unit_dict)
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
            udbuf_rd2pk_cnt = get_ready_to_pick_count("UDBuf.", unit_dict)
            ldbuf_rd2pl_cnt = get_ready_to_place_count("LDBuf.", unit_dict)

            action = no_op
            if loadport_has_wafer and ldbuf_rd2pl_cnt >= 2:
                # loadport pick
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name="LoadPort"
                )
            elif udbuf_rd2pk_cnt >= 2:
                # buffer2 pick
                unit = find_ready_to_pick_in_group("UDBuf.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

    def do_MLR(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["MLR"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:
            wayno = transport.get_wafer(1).waypoint
            ldbuf_rd2pick_cnt = get_ready_to_pick_count("LDBuf.", unit_dict)
            unitA_rd2pl_cnt = get_ready_to_place_count("UnitA.", unit_dict)

            if wayno == 2 and unitA_rd2pl_cnt >= 1:  # LDBuf -> unitA
                unit = find_ready_to_place_in_group("UnitA.", unit_dict)
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
            if wayno == 2:  # LDBuf

                if last_command == CommandType.pick:
                    if get_ready_to_pick_count("LDBuf.", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("LDBuf.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_command == CommandType.place:
                    if get_ready_to_place_count("UnitA.", unit_dict) > 0:
                        unit = find_ready_to_place_in_group("UnitA.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )

            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            ldbuf_rd2pick_cnt = get_ready_to_pick_count("LDBuf.", unit_dict)
            # unitA_rd2pl_cnt = get_ready_to_place_count("UnitA.", unit_dict)

            action = no_op
            # if ldbuf_rd2pick_cnt >= 2 and unitA_rd2pl_cnt >= 2:
            if ldbuf_rd2pick_cnt >= 1:
                # LDBuf -> unit A
                unit = find_ready_to_pick_in_group("LDBuf.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action
        return None

    def do_MUR(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["MUR"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:
            wayno = transport.get_wafer(1).waypoint
            # unitG_rd2pick_cnt = get_ready_to_pick_count("UnitG.", unit_dict)
            udbuf_rd2pl_cnt = get_ready_to_place_count("UDBuf.", unit_dict)

            if wayno == 9 and udbuf_rd2pl_cnt >= 1:  # UnitG -> UDBuf
                unit = find_ready_to_place_in_group("UDBuf.", unit_dict)
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
            if wayno == 9:  # UnitG

                if last_command == CommandType.pick:
                    if get_ready_to_pick_count("UnitG.", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("UnitG.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_command == CommandType.place:
                    if get_ready_to_place_count("UDBuf.", unit_dict) > 0:
                        unit = find_ready_to_place_in_group("UDBuf.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )

            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            unitG_rd2pick_cnt = get_ready_to_pick_count("UnitG.", unit_dict)
            # udbuf_rd2pl_cnt = get_ready_to_place_count("UDBuf.", unit_dict)

            action = no_op
            # if unitG_rd2pick_cnt >= 2 and udbuf_rd2pl_cnt >= 2:
            if unitG_rd2pick_cnt >= 1:
                # LDBuf -> unit A
                unit = find_ready_to_pick_in_group("UnitG.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action
        return None

    def do_ILR(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["ILR"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:
            wayno = transport.get_wafer(1).waypoint
            unitE_rd2pl_cnt = get_ready_to_place_count("UnitE.", unit_dict)

            if unitE_rd2pl_cnt >= 1:
                unit = find_ready_to_place_in_group("UnitE.", unit_dict)
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
            if wayno == 6:  # UnitD

                if last_command == CommandType.pick:
                    if get_ready_to_pick_count("UnitD.", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("UnitD.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_command == CommandType.place:
                    if get_ready_to_place_count("UnitE.", unit_dict) > 0:
                        unit = find_ready_to_place_in_group("UnitE.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )

            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            unitD_rd2pick_cnt = get_ready_to_pick_count("UnitD.", unit_dict)

            action = no_op
            if unitD_rd2pick_cnt >= 1:
                unit = find_ready_to_pick_in_group("UnitD.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action
        return None

    def do_IUR(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["IUR"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        action = no_op
        if transport.wafer_count == 2:
            wayno = transport.get_wafer(1).waypoint
            # unitE_rd2pick_cnt = get_ready_to_pick_count("UnitE.", unit_dict)
            unitF_rd2pl_cnt = get_ready_to_place_count("UnitF.", unit_dict)

            if wayno == 7 and unitF_rd2pl_cnt >= 1:  # UnitE -> UnitF
                unit = find_ready_to_place_in_group("UnitF.", unit_dict)
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
            if wayno == 7:  # UnitE

                if last_command == CommandType.pick:
                    if get_ready_to_pick_count("UnitE.", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("UnitE.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_command == CommandType.place:
                    if get_ready_to_place_count("UnitF.", unit_dict) > 0:
                        unit = find_ready_to_place_in_group("UnitF.", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )

            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            unitE_rd2pick_cnt = get_ready_to_pick_count("UnitE.", unit_dict)

            action = no_op
            if unitE_rd2pick_cnt >= 1:
                unit = find_ready_to_pick_in_group("UnitE.", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action
        return None

    def do_MTR2(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):
        return self.do_MTR234(mtr_no=2, transport_dict=transport_dict, unit_dict=unit_dict)

    def do_MTR3(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):
        return self.do_MTR234(mtr_no=3, transport_dict=transport_dict, unit_dict=unit_dict)

    def do_MTR4(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):
        return self.do_MTR234(mtr_no=4, transport_dict=transport_dict, unit_dict=unit_dict)

    def do_MTR234(self, mtr_no, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict[f"MTR{mtr_no}"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        if transport.wafer_count == 2:

            action = no_op

            wafer_waypoint_no = transport.get_wafer(1).waypoint
            if wafer_waypoint_no == 3:  # UnitA
                unitB_rd2pl_cnt = get_ready_to_place_count(f"UnitB.{mtr_no}_", unit_dict)
                if unitB_rd2pl_cnt >= 1:
                    unit = find_ready_to_place_in_group(f"UnitB.{mtr_no}_", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                    )

            elif wafer_waypoint_no == 4:  # UnitB
                unitC_rd2pl_cnt = get_ready_to_place_count(f"UnitC.{mtr_no}_", unit_dict)
                if unitC_rd2pl_cnt >= 1:
                    unit = find_ready_to_place_in_group(f"UnitC.{mtr_no}_", unit_dict)
                    action = S_ActionMgrInst.find_action_only_for_test(
                        transport.Name, arm_index=1, command=CommandType.place, target_name=unit.Name
                    )
            elif wafer_waypoint_no == 5:  # UnitC
                unitD_rd2pl_cnt = get_ready_to_place_count(f"UnitD.{mtr_no}_", unit_dict)
                if unitD_rd2pl_cnt >= 1:
                    unit = find_ready_to_place_in_group(f"UnitD.{mtr_no}_", unit_dict)
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
            if wayno == 3:  # UnitA
                if last_action_cmd == CommandType.pick:
                    if get_ready_to_pick_count(f"UnitA.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group(f"UnitA.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_action_cmd == CommandType.place:
                    if get_ready_to_place_count(f"UnitB.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_place_in_group(f"UnitB.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )

            elif wayno == 4:  # UnitB
                if last_action_cmd == CommandType.pick:
                    if get_ready_to_pick_count(f"UnitB.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group(f"UnitB.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_action_cmd == CommandType.place:
                    if get_ready_to_place_count(f"UnitC.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_place_in_group(f"UnitC.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )
            elif wayno == 5:  # UnitC
                if last_action_cmd == CommandType.pick:
                    if get_ready_to_pick_count(f"UnitC.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group(f"UnitC.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_action_cmd == CommandType.place:
                    if get_ready_to_place_count(f"UnitD.{mtr_no}_", unit_dict) > 0:
                        unit = find_ready_to_place_in_group(f"UnitD.{mtr_no}_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            unitA_rd2pk_cnt = get_ready_to_pick_count(f"UnitA.{mtr_no}_", unit_dict)
            unitB_rd2pk_cnt = get_ready_to_pick_count(f"UnitB.{mtr_no}_", unit_dict)
            unitC_rd2pk_cnt = get_ready_to_pick_count(f"UnitC.{mtr_no}_", unit_dict)
            unitB_rd2pl_cnt = get_ready_to_place_count(f"UnitB.{mtr_no}_", unit_dict)
            unitC_rd2pl_cnt = get_ready_to_place_count(f"UnitC.{mtr_no}_", unit_dict)
            unitD_rd2pl_cnt = get_ready_to_place_count(f"UnitD.{mtr_no}_", unit_dict)

            action = no_op
            if unitC_rd2pk_cnt >= 2 and unitD_rd2pl_cnt >= 2:
                # unit C pick
                unit = find_ready_to_pick_in_group(f"UnitC.{mtr_no}_", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif unitB_rd2pk_cnt >= 2 and unitC_rd2pl_cnt >= 2:
                # unit B pick
                unit = find_ready_to_pick_in_group(f"UnitB.{mtr_no}_", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            elif unitA_rd2pk_cnt >= 2 and unitB_rd2pl_cnt >= 2:
                # unit B pick
                unit = find_ready_to_pick_in_group(f"UnitA.{mtr_no}_", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )
            assert action != None, "Invalid State"
            return action

    def do_MTR1(self, transport_dict: Dict[str, SimTransport], unit_dict: Dict[str, SimUnit]):

        transport = transport_dict["MTR1"]
        if transport._action_set_flag == True:
            return None

        no_op = S_ActionMgrInst.find_action_only_for_test(transport.Name, arm_index=0, command=CommandType.no_op, target_name="")

        if transport.busy == True:
            return no_op

        if transport.wafer_count == 2:

            action = no_op

            wafer_waypoint_no = transport.get_wafer(1).waypoint
            if wafer_waypoint_no == 8:  # UnitF
                unitB_rd2pl_cnt = get_ready_to_place_count("UnitG.1_", unit_dict)
                if unitB_rd2pl_cnt >= 1:
                    unit = find_ready_to_place_in_group("UnitG.1_", unit_dict)
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
            if wayno == 8:  # UnitF
                if last_action_cmd == CommandType.pick:
                    if get_ready_to_pick_count("UnitF.1_", unit_dict) > 0:
                        unit = find_ready_to_pick_in_group("UnitF.1_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.pick, target_name=unit.Name
                        )
                elif last_action_cmd == CommandType.place:
                    if get_ready_to_place_count("UnitG.1_", unit_dict) > 0:
                        unit = find_ready_to_place_in_group("UnitG.1_", unit_dict)
                        action = S_ActionMgrInst.find_action_only_for_test(
                            transport.Name, arm_index=2, command=CommandType.place, target_name=unit.Name
                        )
            assert action != None, "Invalid State"
            return action

        elif transport.wafer_count == 0:
            unitF_rd2pk_cnt = get_ready_to_pick_count("UnitF.1_", unit_dict)
            # unitG_rd2pl_cnt = get_ready_to_place_count("UnitG.1_", unit_dict)

            action = no_op
            if unitF_rd2pk_cnt >= 1:  # and unitG_rd2pl_cnt >= 2:
                # unit F pick
                unit = find_ready_to_pick_in_group("UnitF.1_", unit_dict)
                action = S_ActionMgrInst.find_action_only_for_test(
                    transport.Name, arm_index=1, command=CommandType.pick, target_name=unit.Name
                )

            assert action != None, "Invalid State"
            return action

    def __call__(self, state_obj: EQState) -> SingleAction:

        self.make_once(state_obj)

        transport_funcs = [
            self.do_IDX,
            self.do_MLR,
            self.do_MUR,
            self.do_MTR1,
            self.do_MTR2,
            self.do_MTR3,
            self.do_MTR4,
            self.do_ILR,
            self.do_IUR,
        ]

        selected_action: SingleAction = None
        for func in transport_funcs:
            selected_action = func(self.transport_dict, self.unit_dict)
            if selected_action != None:
                return selected_action

        assert False, "No action to do."
