from typing import Tuple, Dict
from sim_classes import SimTransport, SimUnit, SimLoadPort, SimAirlock
from action_space import SingleAction, string_to_action_command, CommandType
from s_waypoint_checker import S_WaypointCheckerInst
from s_wafer_process_time_checker import S_WafefProcessingTimeCheckerInst
from s_action_validator import S_ActionValidatorInst, DeadlockState
from s_action_mgr import S_ActionMgrInst
from utils import pos3d
from typing import List
from s_simulator_config import S_SimConfInst


def generate_sim_object(path):
    "Returns: The unit list and transport list are sorted by unit ID, ensuring alignment with their respective list indices."

    S_SimConfInst.parse_configuration(path)

    # generate Sim objects by configuration
    #
    units: List[SimUnit] = []  # fill 0 index as none
    unit_dict = dict()
    inc_id = 1
    dic_units: dict = S_SimConfInst.get_configuration("units")
    for name, attrs in dic_units.items():
        _unit_ = None
        if attrs["type"] == "unit":
            _unit_ = SimUnit(
                id=inc_id,
                name=name,
                unit_type=attrs["type"],
                process_timespan=float(attrs["process_time"]),
                pos=pos3d.make_from_list(attrs["position"]),
            )
            if S_SimConfInst.max_process_time < _unit_._PROECSS_TIMESPAN:
                S_SimConfInst.max_process_time = _unit_._PROECSS_TIMESPAN

        elif attrs["type"] == "loadport":
            _unit_ = SimLoadPort(
                id=inc_id,
                name=name,
                unit_type=attrs["type"],
                process_timespan=attrs["process_time"],
                pos=pos3d.make_from_list(attrs["position"]),
            )

        elif attrs["type"] == "airlock":
            _unit_ = SimAirlock(
                id=inc_id,
                name=name,
                unit_type=attrs["type"],
                process_timespan=attrs["process_time"],
                pos=pos3d.make_from_list(attrs["position"]),
            )

        # elif attrs["type"] == "buffer":
        #     _unit_ = SimBufferSlots(
        #         id=inc_id,
        #         name=name,
        #         unit_type=attrs["type"],
        #         capacity=attrs["capacity"],
        #         process_timespan=int(attrs["process_time"]),
        #         pos=pos3d.make_from_list(attrs["position"]),
        #     )

        units.append(_unit_)
        unit_dict[_unit_.Name] = _unit_
        inc_id += 1

    transports: List[SimTransport] = []  # fill 0 index as none
    transport_dict = dict()
    tid = 1
    dic_transports: dict = S_SimConfInst.get_configuration("transports")
    for name, attrs in dic_transports.items():

        tr = SimTransport(
            id=tid,
            name=name,
            arm_count=attrs["arm_count"],
            pos=pos3d.make_from_list(attrs["position"]),
            velocity=attrs["speed_mm/s"],
        )

        transports.append(tr)
        transport_dict[tr.Name] = tr
        tid += 1

    dic_waypoints: dict = S_SimConfInst.get_configuration("waypoints")
    for way_no, _unit_list in dic_waypoints.items():
        for unit_name in _unit_list:
            unit_dict[unit_name].set_waypoint_list(way_no)
            S_WaypointCheckerInst.append_waypoint(unit_dict[unit_name].ID, unit_name, way_no)
            S_WafefProcessingTimeCheckerInst.set_waypoint_time(way_no, unit_dict[unit_name]._PROECSS_TIMESPAN)
            if S_SimConfInst.max_waypoint < way_no:
                S_SimConfInst.max_waypoint = way_no

    S_WaypointCheckerInst.lock()
    for unit in units:
        if isinstance(unit, SimLoadPort):
            lp: SimLoadPort = unit
            lp.generate_wafer()

    if S_ActionMgrInst.locked == False:
        dic_tr_actions: dict = S_SimConfInst.get_configuration("tr_actions")
        for tr_name, action_list in dic_tr_actions.items():
            for action in action_list:
                target_unit_name = action["unit"]
                tr_id = transport_dict[tr_name].ID
                target_id = 0
                if len(target_unit_name) != 0:
                    target_id = unit_dict[target_unit_name].ID
                command = string_to_action_command(action["command"])
                arm_index = action["arm_index"]
                action = SingleAction(
                    tr_name=tr_name,
                    tr_index=tr_id,
                    command=command,
                    arm_index=arm_index,
                    target_name=target_unit_name,
                    target_index=target_id,
                )
                S_ActionMgrInst.add_action(action)

    S_ActionMgrInst.lock()
    S_ActionValidatorInst.initialize(S_ActionMgrInst.action_count)

    for _action in S_ActionMgrInst.action_list:
        for _tr in transport_dict.values():
            _tr: SimTransport = _tr
            if _action.command != CommandType.no_op and _action.tr_index == _tr.ID:
                _uid = _action.target_index - 1
                if _uid not in _tr.relevant_unit_indices:
                    _tr.relevant_unit_indices.append(_uid)

    if S_ActionValidatorInst.locked == False:
        S_ActionValidatorInst.set_transport_count(tid - 1)

        deadlock_list: list = S_SimConfInst.get_configuration("deadlock")
        for dl in deadlock_list:
            dl_transports = dl[0]
            dl_units = dl[1]
            dl_waypoints = dl[2]
            dl_unit_indices = []
            dl_transport_indices = []
            for unit in dl_units:
                dl_unit_indices.append(unit_dict[unit].ID)
            for transport in dl_transports:
                transport: str = transport
                tr_name = transport.split(".")[0]
                arm_index = int(transport.split(".")[1])
                dl_transport_indices.append((transport_dict[tr_name].ID, arm_index))

            S_ActionValidatorInst.add_deadlock_state(DeadlockState(dl_unit_indices, dl_transport_indices, dl_waypoints))
        S_ActionValidatorInst.lock()

    # scale factor
    max_val = 0.0
    for u in units:
        max_val = max(max_val, u._pos.x, u._pos.y, u._pos.z)
    scale_factor = 1.0 / max_val
    scale_factor = round(scale_factor, 4)
    for u in units:
        u._pos.scale_factor = scale_factor
    for t in transports:
        t._curr_pos.scale_factor = scale_factor
        t._curr_action._target_pos.scale_factor = scale_factor
        t._ori_pos.scale_factor = scale_factor

    S_SimConfInst.pos_scale = scale_factor

    if S_SimConfInst.unit_max_padding == 0:
        S_SimConfInst.unit_max_padding = len(units)
    assert S_SimConfInst.unit_max_padding >= len(units)

    if S_SimConfInst.transport_max_padding == 0:
        S_SimConfInst.transport_max_padding = len(transports)
    assert S_SimConfInst.transport_max_padding >= len(transports)

    S_SimConfInst.max_waypoint_reciprocal = round(1 / S_SimConfInst.max_waypoint, 4)
    S_SimConfInst.max_process_time_reciprocal = round(1 / S_SimConfInst.max_process_time, 4)

    return units, transports


if __name__ == "__main__":

    # parsed_result = parse_configuration("eq_configuration.json")

    # for category, contents in parsed_result.items():
    #     print(f"\n\n### {category} ###")
    #     for key, value in contents.items():
    #         if isinstance(value, str) or isinstance(value, float) or isinstance(value, int):
    #             print(f"  {key}: {value}")
    #         else:
    #             print(f"  [{key}]")
    #             if isinstance(value, list):
    #                 for subvalue in value:
    #                     print(f"   {subvalue}")
    #             elif isinstance(value, dict):
    #                 for subkey, subvalue in value.items():
    #                     print(f"   {subkey}: {subvalue}")

    units, transports = generate_sim_object("eq_configuration.json")

    print("### units")
    for unit in units:
        print(unit.to_string())

    print("### transports")
    for transport in transports:
        print(transport.to_string())

    print("### action_mgr")
    print(S_ActionMgrInst.all_action_to_string())
