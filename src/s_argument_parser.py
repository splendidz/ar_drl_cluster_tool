import argparse
import sys


class S_ArgParser:  # singleton
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_ArgParser()
        return cls._instance

    def __init__(self):
        self.arg_dict = {}

    def initialize(self):
        parser = argparse.ArgumentParser(description="Script to run baseline, evaluation, and wandb logging.")
        parser.add_argument("config", nargs="?", default="./config/model/config.yaml")
        parser.add_argument("--simulator_path", type=str, default="./config/env/simulator.json")
        parser.add_argument("--silent", "-s", action="store_true", default=False)
        parser.add_argument("--baseline", action="store_true", help="whether or not to run baseline action")
        parser.add_argument("--eval_baseline", action="store_true", help="evaluate baseline algorithm")
        parser.add_argument("--eval", type=str, default="", help="evaluation mode. must input saved model path")
        parser.add_argument("--wandb_in_model", action="store_true", default=argparse.SUPPRESS, help="use wandb in model")
        parser.add_argument("--wandb_in_env", action="store_true", default=argparse.SUPPRESS, help="use wandb in simulator env")
        parser.add_argument("--make_schema", action="store_true", help="make expedantic configuration schema.")

        # simulator config
        parser.add_argument("--episode_done_time_sec", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--timestep_interval_sec", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--reward_when_each_wafer_done", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--reward_for_prediction_move", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--reward_wafer_progressing", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--reward_parallel_processing", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--penalty_pending_time", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--penalty_idle_move", type=float, default=argparse.SUPPRESS)

        # model config
        parser.add_argument("--batch_size", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--num_envs", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--total_timestep", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--gamma", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--learning_rate", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--rollout_n_steps", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--ppo_n_epochs", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--ppo_gae_lambda", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--ppo_clip_range", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--ppo_max_grad_norm", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--ppo_ent_coef", type=float, default=argparse.SUPPRESS)
        parser.add_argument("--save_step_log", action="store_true", default=argparse.SUPPRESS)
        parser.add_argument("--eval_freq", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--eval_episode_count", type=int, default=argparse.SUPPRESS)
        parser.add_argument("--wandb_project_name", type=str, default=argparse.SUPPRESS)
        parser.add_argument("--wandb_graph_name", type=str, default=argparse.SUPPRESS)

        args = parser.parse_args()
        self.arg_dict = vars(args)

    @property
    def command_line(self):
        return " ".join(sys.argv)


S_ArgParserInst = S_ArgParser.inst()
