import torch
import torch.nn as nn
import os


class PolicyNetwork_256_128(nn.Module):

    def __init__(self, input_size, output_size):
        super(PolicyNetwork_256_128, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)  # Increased size
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.softmax(self.fc3(x))
        return x


class PolicyNetwork_128_64(nn.Module):

    def __init__(self, input_size, output_size):
        super(PolicyNetwork_128_64, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.softmax(self.fc3(x))
        return x


class HeterogeneousPolicyNetwork(nn.Module):
    def __init__(self, unit_input_size, transport_input_size, num_units, num_transports, output_size):
        super(HeterogeneousPolicyNetwork, self).__init__()

        # Unit processing network
        self.unit_net = nn.Sequential(
            nn.Linear(unit_input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
        )

        # Transport processing network
        self.transport_net = nn.Sequential(
            nn.Linear(transport_input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
        )

        # Final policy network
        self.fc = nn.Sequential(
            nn.Linear(num_units * 32 + num_transports * 32, 128),  # Combine unit and transport features
            nn.ReLU(),
            nn.Linear(128, output_size),
            nn.Softmax(dim=-1),
        )

    def forward(self, units, transports):
        # Process units
        unit_features = self.unit_net(units)  # Shape: [batch_size, num_units, 32]
        unit_features = unit_features.view(unit_features.size(0), -1)  # Flatten: [batch_size, num_units * 32]

        # Process transports
        transport_features = self.transport_net(transports)  # Shape: [batch_size, num_transports, 32]
        transport_features = transport_features.view(transport_features.size(0), -1)  # Flatten: [batch_size, num_transports * 32]

        # Combine unit and transport features
        combined_features = torch.cat([unit_features, transport_features], dim=1)

        # Pass through the final policy network
        return self.fc(combined_features)


class PolicyNetwork_256_128_64(nn.Module):
    def __init__(self, input_size, output_size):
        super(PolicyNetwork_256_128_64, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 256),  # Hidden1
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),  # Hidden2
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),  # Hidden3
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, output_size),  # Output
            # nn.Softmax(dim=-1),  # remove softmax. return as logits. for action mask
        )

    def forward(self, x):
        return self.network(x)

class PolicyNetwork_512_256_128(nn.Module):
    def __init__(self, input_size, output_size):
        super(PolicyNetwork_512_256_128, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Dropout(0.3),  
            nn.Linear(512, 256), 
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),  
            nn.Linear(128, output_size),  # Output
            # No Softmax: Return logits for further processing
        )

    def forward(self, x):
        return self.network(x)
    

class MultiRobotPolicyNetwork(nn.Module):
    def __init__(self, input_size, n_robots, max_actions):
        super(MultiRobotPolicyNetwork, self).__init__()
        self.n_robots = n_robots
        self.max_actions = max_actions

        # Input layer
        self.input_layer = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.LeakyReLU(),  # Changed to LeakyReLU
            nn.LayerNorm(512),
            nn.Dropout(0.4),
        )

        # Hidden layers with residual connections
        self.hidden_layer_1 = nn.Sequential(
            nn.Linear(512, 256),
            nn.LeakyReLU(),  # Changed to LeakyReLU
            nn.LayerNorm(256),
            nn.Dropout(0.3),
        )
        self.hidden_layer_1_residual = nn.Linear(512, 256)  # Project residual to match dimensions

        self.hidden_layer_2 = nn.Sequential(
            nn.Linear(256, 256),
            nn.LeakyReLU(),  # Changed to LeakyReLU
            nn.LayerNorm(256),
            nn.Dropout(0.3),
        )

        self.hidden_layer_3 = nn.Sequential(
            nn.Linear(256, 128),
            nn.LeakyReLU(),  # Changed to LeakyReLU
            nn.LayerNorm(128),
            nn.Dropout(0.3),
        )

        # Output layer
        self.output_layer = nn.Linear(128, n_robots * max_actions)

        # Initialize weights
        self._initialize_weights()

    def forward(self, x):
        # Input layer
        x = self.input_layer(x)

        # Hidden layer 1 with residual connection
        residual = self.hidden_layer_1_residual(x)  # Project residual
        x = self.hidden_layer_1(x)
        x += residual  # Add residual connection

        # Hidden layer 2 with residual connection
        residual = x  # No need to project, dimensions match
        x = self.hidden_layer_2(x)
        x += residual

        # Hidden layer 3
        x = self.hidden_layer_3(x)

        # Output layer
        logits = self.output_layer(x)
        return logits.view(-1, self.n_robots, self.max_actions)  # Shape: [batch_size, n_robots, n_actions_per_robot]

    def _initialize_weights(self):
        """Custom weight initialization for stability."""
        for layer in self.modules():
            if isinstance(layer, nn.Linear):
                nn.init.kaiming_normal_(layer.weight, nonlinearity="leaky_relu")
                nn.init.constant_(layer.bias, 0)


class NetworkParamUtils:

    @classmethod
    def save_model(cls, policy_net: nn.Module, optimizer: torch.optim.Optimizer, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        torch.save(
            {
                "model_state_dict": policy_net.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
            },
            file_path,
        )

    @classmethod
    def load_model(cls, policy_net: nn.Module, optimizer: torch.optim.Optimizer, save_path, device="cpu"):
        checkpoint = torch.load(save_path, map_location=device)
        policy_net.load_state_dict(checkpoint["model_state_dict"])
        if optimizer != None:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    @classmethod
    def save_best_state_action_pairs(cls, states: list, actions: list, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Save the best states-action pairs
        torch.save(
            {
                "states": states,
                "actions": actions,
            },
            file_path,
        )

    @classmethod
    def load_best_state_action_pairs(cls, file_path, device):

        states, actions = [], []
        checkpoint = torch.load(file_path, map_location=device)
        states = checkpoint.get("states", [])
        actions = checkpoint.get("actions", [])

        return states, actions
