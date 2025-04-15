import json
from typing import List


def expand_unit_name_wildcards(ori_unit_names, wildcard_list: List[str]) -> List[str]:

    expanded_units = []
    for item in wildcard_list:
        if "*" in item:
            prefix = item.split("*")[0]  # Get the prefix before the '*'
            expanded_units.extend([unit for unit in ori_unit_names if unit.startswith(prefix)])
        else:
            expanded_units.append(item)

    return expanded_units


# Define a function to load JSON data from a file
def load_json_from_file(file_path):
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


def parse_configuration(file_path):

    parsed_data = load_json_from_file(file_path)

    # Extracting the lists as dictionaries within lists
    args = parsed_data.get("args", {})

    _unit_list_dict: dict = parsed_data.get("unit_list", {})
    _transport_list = parsed_data.get("transport_robot_list", {})
    _waypoint_list = parsed_data.get("waypoint_list", {})
    _action_list = parsed_data.get("action_list", {})

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

    waypoints = {}
    attr_order = _waypoint_list["#attribute"]
    for way_name, attr_list in _waypoint_list.items():
        if way_name == "#attribute":
            continue
        waypoints[way_name] = expand_unit_name_wildcards(unit_name_list, attr_list)

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
                    key_value[attr_order[i]] = expand_unit_name_wildcards(unit_name_list, elem)

            for iter_unit in key_value["unit_list"]:
                new_key_value = {}
                for attr in attr_order:
                    if attr != "unit_list":
                        new_key_value[attr] = key_value[attr]
                    else:
                        new_key_value["unit"] = iter_unit

                tr_actions[tr_name].append(new_key_value)

    parsed_result = {
        "args": args,
        "units": units,
        "transports": transports,
        "waypoints": waypoints,
        "tr_actions": tr_actions,
    }
    return parsed_result


if __name__ == "__main__":

    import pandas as pd

    parsed_result = parse_configuration("eq_configuration.json")

    for category, contents in parsed_result.items():
        print(f"\n\n### {category} ###")
        for key, value in contents.items():
            if isinstance(value, str) or isinstance(value, float) or isinstance(value, int):
                print(f"  {key}: {value}")
            else:
                print(f"  [{key}]")
                if isinstance(value, list):
                    for subvalue in value:
                        print(f"   {subvalue}")
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        print(f"   {subkey}: {subvalue}")
