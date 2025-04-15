from sim_env import EQSimEnv
from sim_classes import EQState, SimUnit, SimLoadPort, SimTransport
from s_wafer_process_time_checker import S_WafefProcessingTimeCheckerInst
from s_waypoint_checker import S_WaypointCheckerInst
from action_space import CommandType
from error_code import ActionResult


class REWARD_FUNCTIONS:

    @staticmethod
    def reward_when_each_wafer_done(env: EQSimEnv) -> float:  # Cycle time reduction
        return env.curr_done_count - env.prev_done_count

    @staticmethod
    def reward_for_prediction_move(env: EQSimEnv) -> float:  # Cycle time reduction
        if env.action_result == ActionResult.hit_the_move:
            return 1
        else:
            return 0

    @staticmethod
    def penalty_idle_move(env: EQSimEnv) -> float:  # Cycle time reduction
        if env.action_result == ActionResult.idle_move:
            return -1
        else:
            return 0

    @staticmethod
    def reward_wafer_progressing(env: EQSimEnv) -> float:  # Cycle time reduction
        return env.curr_progressing - env.prev_progressing

    @staticmethod
    def penalty_pending_time(env: EQSimEnv):
        pending_sum = 0
        for unit in env.state_obj._unit_list:
            unit: SimUnit = unit
            pending_sec = unit.get_pending_time
            pending_sum += pending_sec
        return -1 * (pending_sum * env.frame_sec)

    @staticmethod
    def reward_parallel_processing(env: EQSimEnv) -> float:  # Cycle time reduction

        if env.frame_sec == 0:
            return 0
        parallel_cnt = 0

        for unit in env.state_obj._unit_list:
            unit: SimUnit = unit
            if unit._PROECSS_TIMESPAN > 0:  # processable unit only
                if unit._time_required > 0:
                    parallel_cnt += 1

        return parallel_cnt

    @staticmethod
    def get_progressing_scalar(state_obj: EQState) -> float:

        unit_values = []
        loadport_values = []
        tr_values = []
        for unit in state_obj._unit_list:
            if unit._unit_type == "unit" or unit._unit_type == "airlock":
                unit: SimUnit = unit
                if unit.has_wafer:
                    prev_time = S_WafefProcessingTimeCheckerInst.get_processing_time(unit._curr_waypoint_no, False)
                    # total_processing_time += prev_time + unit._time_required
                    unit_values.append(
                        {
                            "unit": unit.Name,
                            "wayno": unit._curr_waypoint_no,
                            "prev_time": prev_time,
                            "time_req": unit._time_required,
                            "value": prev_time + unit._PROECSS_TIMESPAN - unit._time_required,
                        }
                    )

            elif unit._unit_type == "loadport":
                loadport: SimLoadPort = unit
                done_time = S_WafefProcessingTimeCheckerInst.done_time
                # total_processing_time += loadport.after_process * done_time
                loadport_values.append(
                    {"done_time": done_time, "done_cnt": loadport.after_process, "value": loadport.after_process * done_time}
                )
            else:
                assert False

        for tr in state_obj._transport_list:
            tr: SimTransport = tr
            for wafer in tr.get_wafer_gen():
                prev_time = S_WafefProcessingTimeCheckerInst.get_processing_time(wafer.waypoint, True)
                tr_values.append({"tr": tr.Name, "wayno": wafer.waypoint, "value": prev_time})
                # total_processing_time += prev_time

        total_processing_time = 0
        for o in unit_values:
            total_processing_time += o["value"]
        for o in loadport_values:
            total_processing_time += o["value"]
        for o in tr_values:
            total_processing_time += o["value"]

        # ConsoleLogInst.print_tm(f"{loadport_values}")
        # ConsoleLogInst.print_tm(f"{unit_values}")
        # ConsoleLogInst.print_tm(f"{tr_values}")
        # ConsoleLogInst.print_tm(f"Total Processing : {total_processing_time}")
        return total_processing_time
