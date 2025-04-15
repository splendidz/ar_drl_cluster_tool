from typing import Callable, List, Dict
from s_simulator_config import S_SimConfInst
from utils import S_ConsoleLogInst


class RewardCalculator:
    def __init__(self):
        """Initialize with multiple reward functions and their weights."""
        from reward_functions import REWARD_FUNCTIONS

        self.func_def = {
            "reward_when_each_wafer_done": REWARD_FUNCTIONS.reward_when_each_wafer_done,
            "reward_for_prediction_move": REWARD_FUNCTIONS.reward_for_prediction_move,
            "reward_wafer_progressing": REWARD_FUNCTIONS.reward_wafer_progressing,
            "reward_parallel_processing": REWARD_FUNCTIONS.reward_parallel_processing,
            "penalty_pending_time": REWARD_FUNCTIONS.penalty_pending_time,
            "penalty_idle_move": REWARD_FUNCTIONS.penalty_idle_move,
        }
        self.fn_get_progressing_scalar = REWARD_FUNCTIONS.get_progressing_scalar

        # Convert string function names to actual functions
        self.reward_fns = {self.func_def[name]: weight for name, weight in S_SimConfInst.reward_functions.items()}
        self.use_wafer_progressing = self.reward_fns[REWARD_FUNCTIONS.reward_wafer_progressing] > 0

    def set_reward_functions(self, reward_fns: Dict[Callable, float]):
        """Dynamically change reward functions and their weights."""
        self.reward_fns = reward_fns

    def calculate_reward(self, env) -> float:
        """Compute reward using a weighted sum of multiple reward functions."""
        rewards = 0
        for fn, weight in self.reward_fns.items():
            if weight > 0:
                value = fn(env)
                rewards += weight * value
                # if value != 0:
                #     S_ConsoleLogInst.print_tm(f"func: {fn}, value: {round(value, 3)}, weighted value: {round(weight * value, 3)}")
        #
        # S_ConsoleLogInst.print()
        return rewards

    def get_progressing_scalar(self, state_obj) -> float:
        if self.use_wafer_progressing == False:
            return 0
        return self.fn_get_progressing_scalar(state_obj)
