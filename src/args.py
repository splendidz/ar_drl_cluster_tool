from datetime import datetime
import argparse
import os
import sys
import shutil
import utils
from pathlib import Path
from typing import Literal
from dataclasses import dataclass
from expedantic import ConfigBase


class Args(ConfigBase):

    batch_size: int = 256
    num_envs: int = 8
    total_timestep: int = 8000000
    gamma: float = 0.99
    learning_rate: float = 0.00005
    rollout_n_steps: int = 256
    ppo_n_epochs: int = 10
    ppo_gae_lambda: float = 0.95
    ppo_clip_range: float = 0.2
    ppo_max_grad_norm: float = 0.5
    ppo_ent_coef: float = 0.0
    save_step_log: bool = True
    eval_freq: int = 2000
    eval_episode_count: int = 10
    wandb_in_model: bool = False
    wandb_in_env: bool = False
    wandb_project_name: str = "rl_eq"
    wandb_graph_name: str = ""


class CONFIG:
    """The Expedantic Configuration Object Wrapper."""

    arg: Args = Args()
    loaded = False
    config_path = ""
    simulator_config_file = ""
    path_model_saved_dir = ""
    path_episode_step_log_dir = ""
    path_console_print_dir = ""
    path_run_config_dump_dir = ""

    silent = False
    run_baseline = False
    eval_path = ""
    execution_datetime = None

    @classmethod
    def load(cls):
        # loading once
        if CONFIG.loaded:
            return

        from s_argument_parser import S_ArgParserInst

        CONFIG.loaded = True

        CONFIG.config_path = S_ArgParserInst.arg_dict["config"]
        CONFIG.simulator_config_file = S_ArgParserInst.arg_dict["simulator_path"]
        CONFIG.run_baseline = S_ArgParserInst.arg_dict["baseline"]
        CONFIG.eval_baseline = S_ArgParserInst.arg_dict["eval_baseline"]
        CONFIG.silent = S_ArgParserInst.arg_dict["silent"]
        CONFIG.eval_path = S_ArgParserInst.arg_dict["eval"]
        make_schema_file = S_ArgParserInst.arg_dict["make_schema"]

        assert os.path.exists(f"{CONFIG.config_path}"), f"Config File No Exist - [{CONFIG.config_path}]"
        assert os.path.exists(f"{CONFIG.simulator_config_file}"), f"Simulator File No Exist - [{CONFIG.config_path}]"
        if len(CONFIG.eval_path) > 0:
            assert os.path.exists(f"{CONFIG.eval_path}"), f"Evaluation Model File No Exist - [{CONFIG.eval_path}]"

        branch_path = utils.get_git_info()["branch_name"].split("/")
        branch = branch_path[len(branch_path) - 1]
        # runfile = os.path.basename(sys.argv[0])
        test_name = S_ArgParserInst.arg_dict["wandb_graph_name"] if "wandb_graph_name" in S_ArgParserInst.arg_dict else "run"
        commit_hash = utils.get_git_info()["commit_hash"][0:5]
        CONFIG.execution_datetime = datetime.now()
        now_str = CONFIG.execution_datetime.strftime("%m%d_%H%M%S")

        project_name = (
            S_ArgParserInst.arg_dict["wandb_project_name"] if "wandb_project_name" in S_ArgParserInst.arg_dict else "test_project"
        )
        middle_dir_name = f"[{now_str}]_[{test_name}]_[{commit_hash}]"

        CONFIG.path_console_print_dir = f"./output_data/{project_name}/{middle_dir_name}/"
        CONFIG.path_model_saved_dir = f"./output_data/{project_name}/{middle_dir_name}/network_model/"
        CONFIG.path_episode_step_log_dir = f"./output_data/{project_name}/{middle_dir_name}/episode_log/"
        CONFIG.path_run_config_dump_dir = f"./output_data/{project_name}/{middle_dir_name}/dump_config/"

        os.makedirs(CONFIG.path_console_print_dir, exist_ok=True)
        os.makedirs(CONFIG.path_model_saved_dir, exist_ok=True)
        os.makedirs(CONFIG.path_episode_step_log_dir, exist_ok=True)
        os.makedirs(CONFIG.path_run_config_dump_dir, exist_ok=True)

        try:
            target_path = os.path.join(CONFIG.path_run_config_dump_dir, os.path.basename(CONFIG.config_path))
            shutil.copy(CONFIG.config_path, target_path)
            print(f"copying configuration file succeed: '{CONFIG.config_path}' -> '{target_path}'")
        except Exception as e:
            print(f"copying configuration file failed: {e} - '{target_path}'")

        if make_schema_file:
            # ex "config.schema.yaml"
            schema_path = os.path.join(
                os.path.dirname(CONFIG.config_path),
                Path(CONFIG.config_path).stem + ".schema" + Path(CONFIG.config_path).suffix,
            )
            os.makedirs(os.path.dirname(schema_path), exist_ok=True)
            Args.generate_schema(schema_path)

        if len(CONFIG.config_path) > 0:
            if os.path.exists(CONFIG.config_path) == False:
                os.makedirs(os.path.dirname(CONFIG.config_path), exist_ok=True)
                CONFIG.arg.save_as_yaml(CONFIG.config_path)

            CONFIG.arg = Args.load_from_yaml(CONFIG.config_path)

        # # Change datetime word to now
        for member in dir(CONFIG.arg):
            if not member.startswith("__"):  # Ignore dunder methods/attributes
                value = getattr(CONFIG.arg, member)
                if isinstance(value, str):

                    # newstr = value.replace("<datetime>", currtime)
                    # setattr(CONFIG.arg, member, newstr)

                    # comment replace
                    if value.startswith("#"):
                        setattr(CONFIG.arg, member, "")

    @classmethod
    def change_values(cls, key_val_dict: dict):
        changed_values = {}
        for member in dir(CONFIG.arg):
            if not member.startswith("__"):  # Ignore dunder methods/attributes
                value = getattr(CONFIG.arg, member)
                if member in key_val_dict:
                    new_val = key_val_dict[member]
                    if value != new_val:
                        setattr(CONFIG.arg, member, new_val)
                        changed_values[member] = (value, new_val)

        return changed_values

    @classmethod
    def reset_config_file(cls):
        CONFIG.arg: Args = Args()


# Define a function to load JSON data from a file
def load_json_from_file(file_path):
    import json

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    return None
