import os
from dataclasses import dataclass
from typing import List, Tuple
import json
import shutil
from args import CONFIG
from s_argument_parser import S_ArgParserInst


# @dataclass
class SIM_CONF:
    _instance = None

    @classmethod
    def inst(cls):
        if not cls._instance:
            cls._instance = SIM_CONF()
        return cls._instance

    def __init__(self):
        """these member values are repaced into the simulator json file's args element. (see also "set_arg_attrs")
        If a value doesn't exist in the json file, it will remain as the default value in this code.
        """
        self.__changed_values = {}

        self.max_process_time: float = 0.0
        self.max_process_time_reciprocal: float = 0.0
        self.max_waypoint: int = 0
        self.max_waypoint_reciprocal: int = 0
        self.pick_and_place_time: float = 0.0
        self.timestep_interval_sec: float = 0.0
        self.pos_scale: float = 0.0
        self.unit_max_padding = 0
        self.transport_max_padding = 0
        self.max_arm_count = 2  # fix
        self.episode_done_time_sec = 0
        self.enable_pair_action = False
        self.init_full_wafer = False
        self.random_init_state_count = False
        self.wafer_count = 0
        self.episode_log_periodic_count = False
        self.use_sequential_action_selection = False
        self.reward_functions = {}
        self._configiration = {}

        self.MAX_WAFER_NO: int = 1000
        self.MAX_WAFER_NO_RECIPROCAL = round(1 / self.MAX_WAFER_NO, 5)

    @property
    def is_loaded(self) -> bool:
        return len(self._configiration) != 0

    def set_arg_attrs(self):

        args: dict = self._configiration["args"]

        """simulator json file argument parsing. copy values"""
        # Change datetime word to now
        for member_name in dir(self):
            if member_name.startswith("_"):  # Ignore
                continue

            # member_inst = getattr(self, member_name)
            conf_val = args.get(member_name)
            if conf_val != None:
                setattr(self, member_name, conf_val)

    def change_arg_by_cli_args(self):
        from utils import S_ConsoleLogInst

        def change_dict_val(src_dict, changed_dict):
            for key, value in src_dict.items():
                if isinstance(value, dict):
                    change_dict_val(value, changed_dict)
                else:
                    if key in S_ArgParserInst.arg_dict:
                        val = src_dict[key]
                        new_val = S_ArgParserInst.arg_dict[key]
                        if val != new_val:
                            src_dict[key] = S_ArgParserInst.arg_dict[key]
                            self.__changed_values[key] = (val, new_val)

        args: dict = self._configiration["args"]
        change_dict_val(args, self.__changed_values)

        text = "\n\t".join([f'{k}: "{v[0]}" → "{v[1]}"' for k, v in self.__changed_values.items()])
        S_ConsoleLogInst.print_tm(f" 🟤 Changed simulator parameters: \n\t: {text}")

    def get_configuration(self, name):
        return self._configiration.get(name)

    # Define a function to load JSON data from a file
    def load_json_from_file(self, file_path):
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

    def parse_configuration(self, file_path):

        if self.is_loaded:
            return

        try:
            target_path = os.path.join(CONFIG.path_run_config_dump_dir, os.path.basename(file_path))
            shutil.copy(file_path, target_path)
            print(f"copying simulator config file succeed: '{file_path}' -> '{target_path}'")
        except Exception as e:
            print(f"copying simulator config file failed: {e} - '{target_path}'")
        parsed_data = self.load_json_from_file(file_path)

        # Extracting the lists as dictionaries within lists
        args = parsed_data.get("args", {})

        _unit_list_dict: dict = parsed_data.get("unit_list", {})
        _transport_list = parsed_data.get("transport_robot_list", {})
        _waypoint_list = parsed_data.get("waypoint_list", {})
        _action_list = parsed_data.get("action_list", {})
        _deadlock = parsed_data.get("deadlock", {})

        unit_name_list = []
        units = {}
        attr_order = _unit_list_dict["#attribute"]
        for unit_name, attr_list in _unit_list_dict.items():
            if unit_name == "#attribute":
                continue
            units[unit_name] = {}
            unit_name_list.append(unit_name)
            for i, attr in enumerate(attr_list):
                units[unit_name][attr_order[i]] = attr

        transports = {}
        attr_order = _transport_list["#attribute"]
        for tr_name, attr_list in _transport_list.items():
            if tr_name == "#attribute":
                continue
            transports[tr_name] = {}
            for i, attr in enumerate(attr_list):
                transports[tr_name][attr_order[i]] = attr

        transport_arms = {}
        for tr_name, attr in transports.items():
            arm_cnt = attr["arm_count"]
            for i in range(arm_cnt):
                transport_arms[f"{tr_name}.{i+1}"] = (tr_name, i + 1)

        waypoints = {}
        attr_order = _waypoint_list["#attribute"]
        for way_name, attr_list in _waypoint_list.items():
            if way_name == "#attribute":
                continue
            waypoints[int(way_name)] = self.expand_unit_name_wildcards(unit_name_list, attr_list)

        tr_actions = {}
        attr_order = _action_list["#attribute"]
        for tr_name, attr_list in _action_list.items():
            if tr_name == "#attribute":
                continue
            tr_actions[tr_name] = []
            for attr in attr_list:
                key_value = {}
                for i, elem in enumerate(attr):
                    if attr_order[i] != "unit_list":
                        key_value[attr_order[i]] = elem
                    else:
                        key_value[attr_order[i]] = self.expand_unit_name_wildcards(unit_name_list, elem)

                for iter_unit in key_value["unit_list"]:
                    new_key_value = {}
                    for attr in attr_order:
                        if attr != "unit_list":
                            new_key_value[attr] = key_value[attr]
                        else:
                            new_key_value["unit"] = iter_unit

                    tr_actions[tr_name].append(new_key_value)

        deadlock_list: List[Tuple[List, List]] = []
        for item_list in _deadlock:
            dl_transport_list = item_list["transport"]
            dl_unit_list = self.expand_unit_name_wildcards(unit_name_list, item_list["unit"])
            dl_waypoint_list = item_list["waypoint"]
            deadlock_list.append((dl_transport_list, dl_unit_list, dl_waypoint_list))

        self._configiration = {
            "args": args,
            "units": units,
            "transports": transports,
            "waypoints": waypoints,
            "tr_actions": tr_actions,
            "deadlock": deadlock_list,
        }

        self.change_arg_by_cli_args()
        self.set_arg_attrs()

    def expand_unit_name_wildcards(self, ori_unit_names, wildcard_list: List[str]) -> List[str]:

        expanded_units = []
        for item in wildcard_list:
            if "*" in item:
                prefix = item.split("*")[0]  # Get the prefix before the '*'
                expanded_units.extend([unit for unit in ori_unit_names if unit.startswith(prefix)])
            else:
                expanded_units.append(item)

        return expanded_units


S_SimConfInst = SIM_CONF.inst()
