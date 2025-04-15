from typing import Dict
import os
from args import CONFIG
from s_simulator_config import S_SimConfInst
from utils import S_ConsoleLogInst
import numpy as np


class S_EpisodeLogMgr:  # singleton
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_EpisodeLogMgr()
        return cls._instance

    class _inner_log_:
        def __init__(self):
            self.log_data = []  # string list not flushed yet
            self.episode_no = 1
            self.reward_sum = 0
            self.step_no = 0
            self.timestep = 0
            self.code_step_time_average = 0
            self.is_baseline = False

    def __init__(self):
        self.data_dict: Dict[int, S_EpisodeLogMgr._inner_log_] = {}  # key: env handle
        self.inc_handle = 0
        self.best_reward = float("-inf")
        self.info_file_flag = False

    def make_info_file(self, unit_list, transport_list):
        from sim_classes import SimUnit, SimTransport
        from s_action_mgr import S_ActionMgrInst
        import json

        if self.info_file_flag:
            return
        self.info_file_flag = True  # save only once

        args_root = {}
        unit_root = {}
        transport_root = {}
        action_root = {}

        args_root["max_process_time"] = S_SimConfInst.max_process_time
        args_root["max_waypoint"] = S_SimConfInst.max_waypoint
        args_root["pos_scale"] = S_SimConfInst.pos_scale
        args_root["unit_max_padding"] = S_SimConfInst.unit_max_padding
        args_root["transport_max_padding"] = S_SimConfInst.transport_max_padding

        for unit in unit_list:
            unit: SimUnit = unit
            unit_root[unit.ID] = {
                "ID": unit.ID,
                "Name": unit.Name,
                "Type": unit._unit_type,
                "ProcessTime": unit._PROECSS_TIMESPAN,
                "Position": unit._pos.to_string(),
            }

        for tr in transport_list:
            tr: SimTransport = tr
            transport_root[tr.ID] = {"ID": tr.ID, "Name": tr.Name, "ArmCount": tr._arm_count, "Speed": tr._velocity}

        for i_action, action in enumerate(S_ActionMgrInst.action_list):
            action_root[i_action] = action.to_dict()

        json_root = {"Args": args_root, "Units": unit_root, "Transports": transport_root, "Actions": action_root}
        with open(os.path.join(CONFIG.path_episode_step_log_dir, "info.json"), "w") as json_file:
            json.dump(json_root, json_file, indent=4)

    def create_handle(self, is_baseline=False) -> int:
        self.inc_handle += 1
        handle = self.inc_handle
        self.data_dict[handle] = S_EpisodeLogMgr._inner_log_()
        self.data_dict[handle].is_baseline = is_baseline
        return self.inc_handle

    def reset_episode(self, handle):

        obj = self.data_dict[handle]
        info_dict = {
            "episode": obj.episode_no,
            "reward": obj.reward_sum,
            "step": obj.step_no,
            "timestep": obj.timestep,
            "code_time_step": obj.code_step_time_average,
        }
        if len(obj.log_data) > 0:
            self.flush_log(handle)
            self.data_dict[handle].episode_no += 1

        obj.reward_sum = 0
        obj.timestep = 0
        obj.step_no = 0
        obj.code_step_time_average = 0

    def add_step_log(
        self,
        handle,
        ts,
        total_timestep,
        state_array: np.ndarray,
        i_actions,
        error,
        reward,
        reward_sum,
        code_step_time_average,
        done,
    ):

        if CONFIG.arg.save_step_log == False:
            return

        str_state = str(state_array.tolist())
        obj = self.data_dict[handle]
        obj.reward_sum += reward
        obj.step_no += 1
        obj.timestep = total_timestep
        obj.code_step_time_average = code_step_time_average
        contents = (
            f"[data]\n"
            f"no: {len(obj.log_data)}\n"
            f"timestep: {ts}\n"
            f"total_timestep: {total_timestep}\n"
            f"i_action: {i_actions}\n"
            f"error: {error}\n"
            f"reward: {reward}\n"
            f"reward_sum: {obj.reward_sum}\n"
            f"done: {done}\n"
            f"code_step_time_average: {code_step_time_average}\n"
            f"state: {str_state}\n\n"
        )
        obj.log_data.append(contents)

        obj.reward_sum = reward_sum

        if done:
            self.reset_episode(handle)

    def flush_log(self, handle):

        if CONFIG.arg.save_step_log == False:
            return
        obj = self.data_dict[handle]
        if len(obj.log_data) == 0:
            return

        if obj.is_baseline:
            file_path = os.path.join(
                CONFIG.path_episode_step_log_dir, f"ep{obj.episode_no:04d}_env{handle}_pid{os.getpid()}_baseline.dat"
            )
            with open(file_path, "a") as f:
                f.write("".join(obj.log_data))
            obj.log_data = []
            return
            # S_ConsoleLogInst.print_tm(f"baseline episode step log saved: {file_path}")

        periodic_write = False
        if S_SimConfInst.episode_log_periodic_count > 0:
            periodic_write = obj.episode_no > 1 and obj.episode_no % S_SimConfInst.episode_log_periodic_count == 0

        got_best = self.best_reward < obj.reward_sum

        # write log only got best reward
        if got_best:
            self.best_reward = obj.reward_sum

        if got_best or periodic_write:
            if got_best:
                file_path = os.path.join(
                    CONFIG.path_episode_step_log_dir, f"ep{obj.episode_no:04d}_env{handle}_pid{os.getpid()}_best.dat"
                )
            elif periodic_write:
                file_path = os.path.join(
                    CONFIG.path_episode_step_log_dir, f"ep{obj.episode_no:04d}_env{handle}_pid{os.getpid()}_periodic.dat"
                )

            with open(file_path, "a") as f:
                f.write("".join(obj.log_data))
            S_ConsoleLogInst.print_tm(f"episode step log saved: {file_path}")
        obj.log_data = []


S_EpisodeLogMgrInst = S_EpisodeLogMgr.inst()
