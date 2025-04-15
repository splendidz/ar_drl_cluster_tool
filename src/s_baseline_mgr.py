from typing import Tuple, Dict, List
from state_tensors import EQState
from sim_classes import SimTransport, SimUnit
from action_space import CommandType, SingleAction
from s_action_mgr import S_ActionMgrInst
from s_action_validator import S_ActionValidatorInst
from args import CONFIG
import torch
from utils import S_ConsoleLogInst
import numpy as np
from args import CONFIG
import utils
from collections import defaultdict
import os
import torch
import torch.nn as nn
import torch.optim as optim
import random


class Baseline:
    def __init__(self):

        import baseline_greedy
        import baseline_sim2_greedy

        self.algo = None
        sim_file_name = os.path.basename(CONFIG.simulator_config_file)

        # 50 unit, 9 robot
        if sim_file_name.upper() == "simulator.json".upper():
            self.algo = baseline_sim2_greedy.Greedy()

        # 30 unit, 3 robot
        elif sim_file_name.upper() == "simulator_v2.json".upper():
            self.algo = baseline_greedy.Greedy()

    def select_action(self, state_obj: EQState) -> SingleAction:
        return self.algo(state_obj)

    def get_action(self, env) -> int:

        from sim_env import EQSimEnv

        env: EQSimEnv = env
        action_mask: np.ndarray = S_ActionValidatorInst.get_action_mask(env.observation_state, env.state_obj)

        selected_action = self.select_action(env.state_obj)
        i_action = S_ActionMgrInst.get_action_no(selected_action)
        assert action_mask[i_action] == 1, "action is masked"
        return i_action


class S_BaselineMgr:

    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_BaselineMgr()
        return cls._instance

    def __init__(self):
        self.reward: float = 0.0
        self.done_wafer_count = 0
        self.generated = False

    def run_baseline(self, eval_mode=False, console_out_freq=0):

        # generate once
        if self.generated == True:
            return
        self.generated = True
        # self.baseline_timestep_wp: Dict[Tuple, float] = dict()

        import sim_env
        from s_init_state_mgr import S_InitStateMgrInst

        baseline = Baseline()
        S_ConsoleLogInst.print_tm(f"======= ☘️ Running Baseline Action for Collecting Data ======= ")
        env = sim_env.EQSimEnv(baseline_env=True, eval_mode=eval_mode)

        reward_lst = []
        done_wafer_count_lst = []

        # episode_cnt = 1 if S_RandomInitStateInst.random_set_count <= 0 else S_RandomInitStateInst.random_set_count
        episode_cnt = 1
        for episode in range(episode_cnt):
            state, info = env.reset()
            timestep = info["timestep"]
            i = 0
            done = False
            rewards = 0
            while done == False:

                baseline_action = baseline.get_action(env)
                state, reward, done, _, info = env.step(baseline_action)
                timestep = round(info["timestep"], 3)
                done_wafer_count = info["done_wafer_count"]
                action_str = S_ActionMgrInst.get_action(baseline_action).to_string()
                if console_out_freq > 0:
                    if i % console_out_freq == 0:
                        S_ConsoleLogInst.print_tm(
                            f"Baseline[{i}]: {timestep}sec, reward: {reward}, wafer_cnt: {done_wafer_count} action:[{action_str}]"
                        )
                rewards += reward
                i += 1
                if done:
                    break
            reward_lst.append(rewards)
            done_wafer_count_lst.append(done_wafer_count)
            S_ConsoleLogInst.print_tm(
                f"Baseline EP[{episode}] {timestep}sec, step: {i} reward: {rewards}, wafer_cnt: {done_wafer_count}."
            )

        self.reward = np.mean(reward_lst)
        self.done_wafer_count = np.mean(done_wafer_count_lst)
        S_ConsoleLogInst.print_tm(f"Baseline: reward mean: {self.reward}, done_wafer_mean: {self.done_wafer_count} ")


S_BaselineMgrInst = S_BaselineMgr.inst()

if __name__ == "__main__":
    CONFIG.load()
    S_ConsoleLogInst.set_path(CONFIG.path_console_print_dir)
    S_BaselineMgrInst.run_baseline(False)
