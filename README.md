# Autoregressive DRL for Multi-Robot Scheduling in Semiconductor Cluster Tools

This repository contains the source code accompanying our paper,  
**"Autoregressive DRL for Multi-Robot Scheduling in Semiconductor Cluster Tools"**.

The code implements a reinforcement learning framework for optimizing wafer transfer scheduling in semiconductor manufacturing equipment, specifically in cluster tools involving multiple robots. It leverages an autoregressive policy structure combined with action masking to scale learning across complex, discrete action spaces. The framework is designed to be extensible and includes a configurable simulator supporting various tool configurations.

The implementation supports two representative environments: a radial-type and a track-type cluster tool. Simulation configurations are defined in JSON format, allowing users to easily specify tool layout, robot parameters, action sets, reward weights, and deadlock conditions.

This code is intended for researchers, engineers, and students interested in reinforcement learning, scheduling, and industrial automation.  
The licensing and usage of this code follow the terms described in the accompanying `LICENSE` file.

---

## Simulator Configuration Format

Simulation environments are defined via JSON files. Refer to the sample files under `./config/env/` for structure and examples.

### (1) `args` – Simulator parameters  
Contains general simulation settings such as episode length, reward weights, and time resolution.

```json
"args": {
  "episode_done_time_sec": 1000,
  "timestep_interval_sec": 1.0,
  "init_full_wafer": 1,
  "wafer_count": 1000,
  "reward_functions": {
    "reward_when_each_wafer_done": 1,
    "reward_wafer_progressing": 0.01,
    "penalty_idle_move": 0.0000
  }
}
```

### (2) `unit_list` – Processing modules  
Defines tool modules and their properties, e.g., type, position, and processing time.

### (3) `transport_robot_list` – Robots  
Defines robot properties such as arm count, speed, and initial position.

### (4) `waypoint_list` – Waypoint mapping  
Maps numeric waypoints to module groups. Wildcards (`*`) are supported for auto-matching.

### (5) `action_list` – Robot action sets  
Defines available actions for each robot. Wildcards supported for pattern-based matching.

### (6) `deadlock` – Deadlock conditions  
Defines conditions under which deadlock occurs based on robot state and module availability.

---

## Folder Structure

```
.
├── src/
│   ├── run.sbx.py         # Main training entry point
│   └── sim_env.py         # Environment definition
│
├── config/
│   ├── env/
│   │   ├── radial_type/
│   │   │   └── simulator.json
│   │   └── track_type/
│   │       └── simulator.json
│   └── model/
│       └── config.yaml    # PPO hyperparameters
│
├── StepLogViewer/         # C# Gantt Chart UI (Windows executable)
│                           # Visualizes step logs as shown in the paper
│
├── output_data/           # Logged results after training
│   └── [wandb_project_name]/[run_name]/episode_log/
│                           # Contains Gantt chart step logs recorded based on best reward
│                           # These can be viewed with StepLogViewer for training analysis
│
├── wandb_api.key.txt      # Your wandb API key (user-provided)
└── LICENSE
```

---

## Running the Code

1. **Set up your Weights & Biases API key:**

Save your key in a file:
```
./wandb_api.key.txt
```

2. **Run training with wandb logging:**

```bash
python ./src/run.sbx.py ./config/model/config.yaml \
  --simulator_path ./config/env/[radial_type|track_type]/simulator.json \
  --wandb_in_model \
  --wandb_project_name [your_wandb_project] \
  --wandb_graph_name [run_name]
```

After execution, output logs are saved under:
```
./output_data/[wandb_project_name]/[run_name]/episode_log/
```
These contain step-by-step logs used for the Gantt chart visualization in the paper. You can view these files using the `StepLogViewer` tool.

---

## Citation

If you use this code in your work, please cite our paper:

```
@article{your_citation_entry,
  title={Autoregressive DRL for Multi-Robot Scheduling in Semiconductor Cluster Tools},
  author={Your Name and Others},
  journal={...},
  year={2024}
}
```
---

## Author

This code was developed as part of the research presented in the paper  
**"Autoregressive DRL for Multi-Robot Scheduling in Semiconductor Cluster Tools"**.

For questions or collaboration inquiries, please contact:  
**Soo-Hwan Cho** – soohwancho@korea.ac.kr  
Affiliation: Korea University, High Performance Intelligence Computing (HPIC) Lab

---

## License

This project is licensed under the terms described in the `LICENSE` file.

