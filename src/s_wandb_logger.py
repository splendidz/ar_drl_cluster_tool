import wandb
from args import CONFIG
import sys
import utils
import os
from datetime import datetime


class S_WandbLogger:
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_WandbLogger()
        return cls._instance

    def __init__(self):
        self._initialized = False

    @staticmethod
    def get_graph_name():

        cur_time = CONFIG.execution_datetime
        if cur_time == None:
            cur_time = datetime.now()
        branch = utils.get_git_info()["branch_name"]
        runfile = os.path.basename(sys.argv[0])
        commit_hash = utils.get_git_info()["commit_hash"][0:5]
        now_str = cur_time.strftime("%mM%dD_%H:%M:%S")

        if len(CONFIG.arg.wandb_graph_name) != 0:
            graph_name = f"[{now_str}]_[{CONFIG.arg.wandb_graph_name}]_[{commit_hash}]"
        else:
            graph_name = f"[{now_str}]_[{runfile}]_[{branch}]_[{commit_hash}]"

        return graph_name

    def initialize(self, force=False):

        if self._initialized and force == False:
            return

        if CONFIG.arg.wandb_in_env or CONFIG.arg.wandb_in_model:

            try:
                with open("./wandb_api_key.txt", "r") as f:
                    api_key = f.read().strip()
            except:
                print("[ERROR] Cannot load wandb_api_key.txt")
                return

            # Set the WANDB_API_KEY environment variable
            os.environ["WANDB_API_KEY"] = api_key
            graph_name = S_WandbLogger.get_graph_name()
            assert len(CONFIG.arg.wandb_project_name) > 0, "Wandb project name is needed in the config file."
            # wandb.login(key=CONFIG.arg.wandb_key)
            run = wandb.init(
                config=CONFIG.arg.model_dump(),
                project=CONFIG.arg.wandb_project_name,
                name=graph_name,
                settings={"disable_code": True},
            )

            utils.S_ConsoleLogInst.print_tm(f"✍️  wandb: Project Name: {run.project}")
            utils.S_ConsoleLogInst.print_tm(f"✍️  wandb: Run Name: {run.name}")
            utils.S_ConsoleLogInst.print_tm(f"✍️  wandb: Run ID: {run.id}")
            utils.S_ConsoleLogInst.print_tm(f"✍️  wandb: Entity (Team/User): {run.entity}")
            utils.S_ConsoleLogInst.print_tm(f"✍️  wandb: Run URL: {run.url}")

        self._initialized = True

    def log(self, data):
        if (CONFIG.arg.wandb_in_env or CONFIG.arg.wandb_in_model) and self._initialized:
            wandb.log(data)

    def reconnect(self):
        wandb.finish()
        self.initialize(force=True)


S_WandbLoggerInst = S_WandbLogger.inst()
