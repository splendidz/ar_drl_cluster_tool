from typing import Any
import numpy as np
from gymnasium.wrappers.common import TimeLimit
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
import wandb
from wandb.integration.sb3 import WandbCallback
from sim_env import EQSimEnv
from s_action_validator import S_ActionValidatorInst
from args import CONFIG
from utils import S_ConsoleLogInst
import os


class EQEvalCallback(MaskableEvalCallback):
    def _log_success_callback(self, locals_: dict[str, Any], globals_: dict[str, Any]) -> None:
        info = locals_["info"]

        if locals_["done"]:
            self.logger.record("eval/done_wafer_count", info["done_wafer_count"])
            self.logger.record("eval/reward", info["reward_sum"])
            self.logger.record("eval/reward_sub_baseline", info["reward_sub_baseline"])
            self.logger.record("eval/wafer_done_count_sub_baseline", info["wafer_done_count_sub_baseline"])
            self.logger.record("eval/moving_dist", info["moving_dist"])


def mask_fn(env: EQSimEnv) -> np.ndarray:
    mask = S_ActionValidatorInst.get_action_mask(None, env.state_obj)  # type: ignore
    return mask


def vec_mask_fn(env) -> np.ndarray:

    def get_unwrapped_env(single_env):
        """Unwrap the environment to access the original EQSimEnv instance."""
        while hasattr(single_env, "env"):
            single_env = single_env.env  # Keep unwrapping
        return single_env

    if hasattr(env, "envs"):  # Vectorized case
        masks = np.array([S_ActionValidatorInst.get_action_mask(None, get_unwrapped_env(e).state_obj) for e in env.envs])
    else:  # Single environment case
        original_env = get_unwrapped_env(env)
        masks = np.array([S_ActionValidatorInst.get_action_mask(None, original_env.state_obj)])

    return masks  # Shape: (num_envs, action_dim)


def train():
    def make_env():
        # return ActionMasker(EQSimEnv(), mask_fn)  # type:ignore
        env = EQSimEnv()
        env = ActionMasker(env, mask_fn)  # type: ignore
        # env = TimeLimit(env, 3000)
        return env

    verbose = 0 if CONFIG.silent else 1

    envs = make_vec_env(make_env, n_envs=CONFIG.arg.num_envs)
    env_for_eval = Monitor(make_env())

    my_callback: list[BaseCallback] = []
    if CONFIG.arg.eval_freq > 0:
        my_callback.append(
            EQEvalCallback(env_for_eval, eval_freq=CONFIG.arg.eval_freq, n_eval_episodes=1, deterministic=True, verbose=verbose)
        )
    if CONFIG.arg.wandb_in_model:
        my_callback.append(WandbCallback(verbose=verbose))

    # make and init model
    model = MaskablePPO(
        policy="MlpPolicy",
        env=envs,
        learning_rate=CONFIG.arg.learning_rate,
        n_steps=CONFIG.arg.rollout_n_steps,
        batch_size=CONFIG.arg.batch_size,
        n_epochs=CONFIG.arg.ppo_n_epochs,
        gamma=CONFIG.arg.gamma,
        gae_lambda=CONFIG.arg.ppo_gae_lambda,
        clip_range=CONFIG.arg.ppo_clip_range,
        max_grad_norm=CONFIG.arg.ppo_max_grad_norm,
        ent_coef=CONFIG.arg.ppo_ent_coef,
        verbose=verbose,
        device="auto",
        tensorboard_log=".tb/",
        policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256])),
        # policy_kwargs=dict(net_arch=dict(pi=[256, 256, 128], vf=[256, 256, 128])),
    )

    try:

        S_ConsoleLogInst.print_tm("\n\n🌱 PPO Traning Start!")
        model.learn(
            total_timesteps=CONFIG.arg.total_timestep,
            callback=my_callback,
            progress_bar=True,
        )
        S_ConsoleLogInst.print_tm("======= PPO Training Done. ======== ")

        model_save_path = os.path.join(CONFIG.path_model_saved_dir, "MaskablePPO")
        model.save(model_save_path)
        S_ConsoleLogInst.print_tm(f'Model Saved.\n\t -> "{model_save_path}".')

    except KeyboardInterrupt:
        model_save_path = os.path.join(CONFIG.path_model_saved_dir, "MaskablePPO_ud")  # ud: undone
        model.save(model_save_path)
        S_ConsoleLogInst.print_tm(f'Model Saved.\n\t -> "{model_save_path}".')
        print("Training interrupted by user.")
        return

    setup_eval()
    evaluate(model_save_path)


def setup_eval():
    from s_simulator_config import S_SimConfInst

    CONFIG.arg.wandb_in_env = True
    CONFIG.arg.wandb_graph_name += "_eval"

    S_SimConfInst.timestep_interval_sec = 0.1
    S_SimConfInst.episode_done_time_sec = 3600
    S_WandbLoggerInst.reconnect()


def evaluate(model_path):

    def make_eval_env():
        return EQSimEnv(eval_mode=True)

    env = make_vec_env(make_eval_env, n_envs=1)
    model = MaskablePPO.load(model_path, env=env)
    model.set_env(env)
    obs = env.reset()
    dones = np.zeros(1, dtype=bool)

    S_ConsoleLogInst.print_tm("\n\n🚀  PPO Evaluation Start!")

    while not np.any(dones):
        action_mask = vec_mask_fn(env)
        action, _ = model.predict(obs, deterministic=True, action_masks=action_mask)
        obs, rewards, dones, infos = env.step(action)

    print(f"======== Evaluation completed. ========= ")


if __name__ == "__main__":

    import global_init
    from s_wandb_logger import S_WandbLoggerInst

    global_init.initialize()
    if len(CONFIG.eval_path):
        evaluate(CONFIG.eval_path)
    else:
        if CONFIG.arg.wandb_in_model:
            with wandb.init(
                config=CONFIG.arg.model_dump(exclude={"wandb_key"}),
                entity="mycpp-korea-university",
                project=CONFIG.arg.wandb_project_name,
                name=S_WandbLoggerInst.get_graph_name(),
                sync_tensorboard=True,
                settings={"disable_code": True},
            ):
                train()
        else:
            train()
