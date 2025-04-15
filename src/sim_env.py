from typing import Tuple, Dict, List
import numpy as np
import copy
import gymnasium as gym
from gymnasium.spaces import Discrete, Box

# from gymnasium.spaces import MultiDiscrete
# import gym as gym
# from gym.spaces import Discrete, Box
# from gym.spaces import MultiDiscrete
from args import CONFIG
from error_code import ErrorCode, ActionResult
from state_tensors import EQState
from sim_classes import SimTransport, SimUnit, SimLoadPort
from sim_data_loader import generate_sim_object
from action_space import CommandType
import utils
from utils import ceil_to_decimal_place, S_ConsoleLogInst
from s_action_mgr import S_ActionMgrInst, SingleAction
from s_waypoint_checker import S_WaypointCheckerInst
from s_wafer_process_time_checker import S_WafefProcessingTimeCheckerInst
from s_action_validator import S_ActionValidatorInst
from s_simulator_config import S_SimConfInst
from s_episode_log_mgr import S_EpisodeLogMgrInst
from s_baseline_mgr import S_BaselineMgrInst
from s_wandb_logger import S_WandbLoggerInst
from s_init_state_mgr import S_InitStateMgrInst
from reward_calculator import RewardCalculator


#####################################
## Equipment Environment Simulator
##
class EQSimEnv(gym.Env):
    """Equipment Environment Simulator"""

    def __init__(self, baseline_env=False, eval_mode=False):
        super(EQSimEnv, self).__init__()
        self.baseline_mode = baseline_env
        self.eval_mode = eval_mode
        S_WandbLoggerInst.initialize()
        unit_list, transport_list = generate_sim_object(CONFIG.simulator_config_file)
        self.state_obj = EQState(unit_list=unit_list, transport_list=transport_list)
        self.state_obj.reset()
        S_InitStateMgrInst.initialize(self.state_obj)
        self.random_init_handle = S_InitStateMgrInst.create_handle()
        S_WafefProcessingTimeCheckerInst.calculate(unit_list, transport_list)
        self.log_handle = S_EpisodeLogMgrInst.create_handle(self.baseline_mode)
        S_EpisodeLogMgrInst.make_info_file(unit_list, transport_list)
        self.observation_state: np.ndarray = self.state_obj.get_observation_state()
        self.observation_space = Box(low=0.0, high=1.0, shape=(len(self.observation_state),), dtype=np.float32)
        self.action_space = Discrete(S_ActionMgrInst.action_count)
        # self.action_space = MultiDiscrete([S_ActionMgrInst.action_count] * self.state_obj.transport_count)
        self.ep_cnt = 0
        self.action = SingleAction()
        self.reward_calculator = RewardCalculator()
        self.reset_epsiode_values()

    def reset(self, seed=None, options=None):
        """Resets the environment to an initial state and returns an initial observation."""

        S_EpisodeLogMgrInst.reset_episode(self.log_handle)
        self.print_episode_log()
        self.ep_cnt += 1
        self.reset_epsiode_values()
        self.state_obj.reset()
        S_InitStateMgrInst.make_init_state(self.random_init_handle, self.state_obj)
        self.process_timestep(0)
        self.observation_state = self.state_obj.get_observation_state()
        self.action_mask = S_ActionValidatorInst.get_action_mask(self.observation_state, self.state_obj)
        self.make_info()

        return self.observation_state, self.info  # Returns the initial observation

    def reset_epsiode_values(self):
        self._tmeasure_avg = 0.0
        self.i_action = 0
        self.no_wafer_in_eq = False
        self.reach_cycle_time = False
        self.reward = 0
        self.done = False
        self.err_code = ErrorCode.ok
        self.frame_sec = 0
        self.action_mask = None
        self.prev_logging_time = 0
        self.info = {}
        self.step_count = 0
        self.reward_sum = 0
        self.curr_done_count = 0
        self.prev_done_count = 0
        self.curr_progressing = 0
        self.prev_progressing = 0
        self.action_result = ActionResult.ok
        self.moving_distance = 0
        # self.parallel_processing_cnt = 0
        # self.prev_parallel_processing_cnt = 0
        # self.curr_pending_time = 0
        # self.prev_pending_time = 0
        self.action.reset()

    def step(self, i_action: int):

        _t_start = utils.start_measure()
        self.step_count += 1
        self.action_result = ActionResult.ok
        self.err_code = ErrorCode.ok

        self.i_action = i_action
        self.action = S_ActionMgrInst.get_action(i_action)

        self.err_code = S_ActionValidatorInst.check_action(self.state_obj, i_action)
        if self.err_code == ErrorCode.ok:
            transport: SimTransport = self.state_obj.get_transport(self.action.tr_index)
            self.action_result = transport.set_action(self.state_obj, self.action)
        else:
            S_ConsoleLogInst.print_tm(
                f"[ERROR] *** INVALD ACTION OCCURS - action no: {i_action}, action: {self.action.to_string()}, {self.err_code.name} ***"
            )

        self.state_obj.current_action_tr_idx += 1
        if self.state_obj.current_action_tr_idx > self.state_obj.transport_count:
            self.state_obj.current_action_tr_idx = 1  # reset to the first

        # 0 means update status
        # > 0 means process time as much as the number of seconds.
        self.frame_sec = 0

        all_action_set = all(_t._action_set_flag for _t in self.state_obj._transport_list)
        # process time only when set all transport action
        if all_action_set:
            # discret(next event) timer
            if S_SimConfInst.timestep_interval_sec == 0.0:
                next_eval_timestep = S_SimConfInst.episode_done_time_sec - self.state_obj.current_timestep
                self.frame_sec = self.get_next_event_time(next_eval_timestep)
                self.frame_sec = round(self.frame_sec, 5)
            # fixed n-second periodic timer
            else:
                self.frame_sec = S_SimConfInst.timestep_interval_sec

        # # # # # # # # # # # # # # # # # # # # # # # #
        self.process_timestep(self.frame_sec)
        # # # # # # # # # # # # # # # # # # # # # # # #
        self.state_obj.current_timestep += self.frame_sec

        self.observation_state = self.state_obj.get_observation_state()
        self.action_mask = S_ActionValidatorInst.get_action_mask(self.observation_state, self.state_obj)

        self.no_wafer_in_eq = self.state_obj.is_done()
        self.reach_cycle_time = self.state_obj.current_timestep >= S_SimConfInst.episode_done_time_sec
        self.done = self.no_wafer_in_eq or self.reach_cycle_time

        self.curr_progressing = self.reward_calculator.get_progressing_scalar(self.state_obj)
        self.curr_done_count = self.get_done_wafer_count(self.state_obj)
        # reward
        self.reward = self.reward_calculator.calculate_reward(self)

        self.reward_sum += self.reward
        self.prev_progressing = self.curr_progressing
        self.prev_done_count = self.curr_done_count
        force_wandb_log_flag = False
        if self.eval_mode:
            if self.state_obj.current_timestep - self.prev_logging_time > 1.0:
                self.prev_logging_time = self.state_obj.current_timestep
                force_wandb_log_flag = True

        self._tmeasure_avg = utils.get_cumulative_mean(self._tmeasure_avg, utils.get_elapsed_ms(_t_start), self.step_count)
        self.make_info()
        self.step_log()
        self.wandb_log(force_write=force_wandb_log_flag, print_console=self.eval_mode)
        if self.done:
            S_EpisodeLogMgrInst.reset_episode(self.log_handle)

        return self.observation_state, self.reward, self.done, False, self.info

    def get_next_event_time(self, next_evaluation_time) -> float:
        """Returns nearest next event time to time jump."""

        req_times = [float("inf")]
        req_times.extend([tr._time_required for tr in self.state_obj._transport_list if tr._time_required > 0])
        req_times.extend([unit._time_required for unit in self.state_obj._unit_list if unit._time_required > 0])
        near_future_step = min(req_times)

        if near_future_step == float("inf"):
            near_future_step = next_evaluation_time
        elif near_future_step > next_evaluation_time:
            near_future_step = next_evaluation_time

        ceiled_timestep = ceil_to_decimal_place(near_future_step, 3)
        if ceiled_timestep == 0:
            ceiled_timestep = 0.1
        return ceiled_timestep

    def render(self, mode=""):
        return self.state_obj.to_string()

    def close(self):
        """Cleans up resources."""
        pass

    def process_timestep(self, processing_time: float):
        """process T timestep"""

        for unit in self.state_obj._unit_list:
            unit: SimUnit = unit
            left_time = unit.time_elapsed(processing_time)

        for transport in self.state_obj._transport_list:
            transport: SimTransport = transport
            self.moving_distance += transport.time_elapsed(processing_time)

    def get_done_wafer_count(self, state_obj: EQState) -> int:

        for unit in state_obj._unit_list:
            unit: SimUnit = unit
            if unit._unit_type == "loadport":
                loadport: SimLoadPort = unit
                return loadport.after_process
        return 0

    def make_info(self):

        self.info = {
            "action_mask": self.action_mask,
            "timestep": self.state_obj.current_timestep,
            "error_code": self.err_code,
            "error_value": self.err_code.value,
            "reward_sum": self.reward_sum,
            "code_step_time_average": self._tmeasure_avg,
            "no_wafer_in_eq": self.no_wafer_in_eq,
            "reach_reward_time": self.reach_cycle_time,
            "done_wafer_count": self.curr_done_count,
            "reward_sub_baseline": self.reward_sum - S_BaselineMgrInst.reward,
            "wafer_done_count_sub_baseline": self.curr_done_count - S_BaselineMgrInst.done_wafer_count,
            "moving_dist": self.moving_distance,
        }

    def step_log(self):

        S_EpisodeLogMgrInst.add_step_log(
            handle=self.log_handle,
            ts=self.frame_sec,
            total_timestep=round(self.state_obj.current_timestep, 3),
            state_array=self.observation_state,
            i_actions=self.i_action,
            error=self.err_code.name,
            reward=self.reward,
            reward_sum=round(self.reward_sum, 2),
            code_step_time_average=self._tmeasure_avg,
            done=self.done,
        )

    def wandb_log(self, force_write=False, print_console=False):

        if CONFIG.arg.wandb_in_env == False:
            return

        if self.done or force_write:
            reward_sub_bs = round(self.reward_sum - S_BaselineMgrInst.reward, 4)
            done_wafer_sub_bs = round(self.curr_done_count - S_BaselineMgrInst.done_wafer_count, 4)

            if S_BaselineMgrInst.reward == 0:
                reward_sub_bs = done_wafer_sub_bs = 0

            func = self.reward_calculator.func_def["reward_parallel_processing"]
            if self.eval_mode:
                parallel_units_cnt = func(self)
                log_data = {
                    "episode/timestep": round(self.state_obj.current_timestep, 4),
                    "episode/reward": round(self.reward_sum, 4),
                    "episode/done_wafer_count": self.curr_done_count,
                    "episode/parallel_units_cnt": parallel_units_cnt,
                    "episode/moving_distance": self.moving_distance,
                }
            else:
                log_data = {
                    "episode/reward": round(self.reward_sum, 4),
                    "episode/step_time": self._tmeasure_avg,
                    "episode/done_wafer_count": self.curr_done_count,
                    "episode/reward_sub_bs": reward_sub_bs,
                    "episode/done_wafer_sub_bs": done_wafer_sub_bs,
                    "episode/moving_distance": self.moving_distance,
                }

            S_WandbLoggerInst.log(log_data)
            if print_console:
                S_ConsoleLogInst.print_tm(log_data)

    def print_episode_log(self):
        file_info_dict = {
            "EnvID": self.log_handle,
            "EP": self.ep_cnt,
            "Step": self.step_count,
            "Timestep": self.state_obj.current_timestep,
            "Done": self.done,
            "Reward": self.reward_sum,
            "Done Wafer Cnt": self.curr_done_count,
            "moving_distance": self.moving_distance,
            "Code Time ms": self._tmeasure_avg,
        }
        S_ConsoleLogInst.print_only_file(file_info_dict)


def make_env():
    return EQSimEnv()
