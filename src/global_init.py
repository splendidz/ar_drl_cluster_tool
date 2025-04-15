from args import CONFIG
from utils import S_ConsoleLogInst
from s_episode_log_mgr import S_EpisodeLogMgrInst
from s_baseline_mgr import S_BaselineMgrInst
from s_wandb_logger import S_WandbLoggerInst
import sys


def initialize():

    from s_argument_parser import S_ArgParserInst
    from s_simulator_config import S_SimConfInst

    S_ArgParserInst.initialize()
    CONFIG.load()
    S_ConsoleLogInst.set_path(CONFIG.path_console_print_dir)
    S_ConsoleLogInst.print_tm(f" 🟤 Input command line argument: \n\t: {S_ArgParserInst.command_line}")
    text = "\n\t".join([f"{k}: {v}" for k, v in S_ArgParserInst.arg_dict.items()])
    S_ConsoleLogInst.print_tm(f" 🟤 Parsed Arguments: \n\t: {text}")

    changed_values = CONFIG.change_values(S_ArgParserInst.arg_dict)
    text = "\n\t".join([f'{k}: "{v[0]}" → "{v[1]}"' for k, v in changed_values.items()])
    S_ConsoleLogInst.print_tm(f" 🟤 Changed model parameters: \n\t: {text}")

    S_WandbLoggerInst.initialize()

    if CONFIG.run_baseline:
        S_BaselineMgrInst.run_baseline()

    elif CONFIG.eval_baseline:
        S_BaselineMgrInst.run_baseline(eval_mode=True)
        sys.exit()
