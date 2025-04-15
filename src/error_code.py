from enum import Enum


class ErrorCode(Enum):
    ok = 0
    busy_transport = 1
    busy_unit = 2
    unreachable_pos = 3
    occupied_transport = 4
    occupied_unit = 5
    empty_transport = 6
    empty_unit = 7
    non_sequencial_waypoint = 8
    unit_no_exists = 9
    deadlock = 10
    already_set_action = 11
    action_ownership_error = 12  #  the action is not owned by the current robot.
    step_limit = 13
    pair_action_needed = 14  # must follow previous arm action
    unsequential_action_turn = 15  # not the turn of the transport


class ActionResult(Enum):
    ok = 0
    idle_move = 1
    invalid_action = 2
    hit_the_move = 3
