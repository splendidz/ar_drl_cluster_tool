from typing import List
import copy
from utils import S_ConsoleLogInst
from action_space import SingleAction, CommandType


class S_ActionMgr:  # singleton

    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = S_ActionMgr()
        return cls._instance

    def __init__(self):
        self.clear()
        self.action_list: List[SingleAction] = []  # action tuple
        self._action_dict_for_test = dict()  # only for test. don't use it in the logic.
        self.locked = False

    def clear(self):
        self.action_list: List[SingleAction] = []  # action tuple

    @property
    def action_count(self):
        return len(self.action_list)

    def add_action(self, action: SingleAction) -> bool:
        if self.locked:
            return False
        self.action_list.append(action)

        # only for test
        self._action_dict_for_test[(action.tr_name, action.arm_index, action.command.value, action.target_name)] = action
        return True

    def find_action_only_for_test(self, tr_name: str, arm_index: int, command: CommandType, target_name: str) -> SingleAction:
        return self._action_dict_for_test.get((tr_name, arm_index, command.value, target_name))

    def find_action_num_only_for_test(self, tr_name: str, arm_index: int, command: CommandType, target_name: str) -> int:
        action = self._action_dict_for_test.get((tr_name, arm_index, command.value, target_name))
        assert action
        return self.action_list.index(action)

    def find_actions(self, command: CommandType, target_name: str) -> List[SingleAction]:
        result = []
        for i, iter_action in enumerate(self.action_list):
            if iter_action.command == command and iter_action.target_name == target_name:
                result.append(copy.deepcopy(iter_action))

        return result

    def lock(self):
        if self.locked == False:
            S_ConsoleLogInst.print_tm(f"Action Manager Locked. Action Count: {len(self.action_list)}")
            self.locked = True

    def get_action(self, i_action, do_copy=True) -> SingleAction:
        if i_action < 0 or i_action >= len(self.action_list):
            return None
        if do_copy:
            return copy.deepcopy(self.action_list[i_action])
        else:
            return self.action_list[i_action]

    def get_action_no(self, action: SingleAction) -> int:
        for i, iter_action in enumerate(self.action_list):
            if iter_action.compare(action) == True:
                return i
        return -1

    def all_action_to_string(self, prefix="") -> str:
        lst = []
        for action in self.action_list:
            lst.append(action.to_string())
        return f"\n{prefix}".join(lst)

    def i_action_list_to_string(self, i_action_list: List[int]) -> List[str]:
        lst = []
        for i in i_action_list:
            lst.append(self.get_action(i_action=i).to_string())
        return lst


S_ActionMgrInst = S_ActionMgr.inst()
