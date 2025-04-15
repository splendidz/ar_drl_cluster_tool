from enum import Enum
from utils import pos3d
import numpy as np


class CommandType(Enum):
    no_op = 0
    pick = 1
    place = 2
    move = 3


def string_to_action_command(s) -> CommandType:
    for cmd in CommandType:
        if cmd.name == s:
            return cmd
    return "[unknown]"


class SingleAction:
    def __init__(self, tr_name="", tr_index=0, command=CommandType.no_op, arm_index=0, target_name="", target_index=0):
        self.tr_name = tr_name
        self.command: CommandType = command
        self.arm_index = arm_index
        self.target_name = target_name
        self.tr_index = tr_index
        self.target_index = target_index
        self._tag = None
        self._target_pos = pos3d.EmptyPos()

    def copy_from(self, action):
        self.tr_name = action.tr_name
        self.command: CommandType = action.command
        self.arm_index = action.arm_index
        self.target_name = action.target_name
        self.tr_index = action.tr_index
        self.target_index = action.target_index
        self._tag = None
        self._target_pos.update_position(action._target_pos)

    def reset(self):
        self.tr_name = ""
        self.command: CommandType = CommandType.no_op
        self.arm_index = 0
        self.target_name = ""
        self.tr_index = 0
        self.target_index = 0
        self._tag = None

    def compare(self, action: "SingleAction") -> bool:
        if self.tr_name != action.tr_name:
            return False
        if self.command != action.command:
            return False
        if self.arm_index != action.arm_index:
            return False
        if self.target_name != action.target_name:
            return False
        return True

    # def to_tensor(self, device):
    #     # One-hot encode the command type
    #     cmd_tensor = F.one_hot(torch.tensor(self.command.value, device=device), num_classes=len(CommandType))
    #     cmd_tensor.to(torch.float32)

    #     # Concatenate all tensors into a single tensor
    #     return torch.cat([cmd_tensor, self._target_pos.to_tensor(device)])

    def to_array(self) -> np.ndarray:
        # One-hot encode the command type using NumPy
        cmd_one_hot = np.zeros(len(CommandType), dtype=float)
        cmd_one_hot[self.command.value] = 1.0
        target_pos = self._target_pos.get_scaled_pos()

        data = np.concatenate([cmd_one_hot, target_pos])

        return data

    def to_string(self, prefix=""):
        return f"{self.tr_name}.{self.arm_index}, {self.command.name}, target:{self.target_name}"

    def to_dict(self):
        return {
            "tr_name": self.tr_name,
            "command": self.command.name,
            "arm_index": self.arm_index,
            "target_name": self.target_name,
        }
