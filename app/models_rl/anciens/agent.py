import torch
import torch.nn as nn
import torch.optim as optim
import random
import math
import numpy as np
from common.memory import ReplayBuffer
from common.model import CNN, MLP

class DQN:
    """

    Attributes:
        state_dim: 
        action_dim: 
        device: 
        gamma: 
        frame_idx: 
        epsilon: 
        batch_size: 
        policy_net: 
        target_net: 
        optimizer: 
        memory: 
    """
    
    def __init__(self, state_dim, action_dim, cfg):

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = cfg.device
        self.gamma = cfg.gamma

        # e-greedy 
        # 
        self.frame_idx = 0
        # lambda 
        self.epsilon = lambda frame_idx: cfg.epsilon_end + \
            (cfg.epsilon_start - cfg.epsilon_end) * \
            math.exp(-1. * frame_idx / cfg.epsilon_decay)

        self.batch_size = cfg.batch_size

        self.policy_net = CNN(state_dim, action_dim).to(self.device)
        self.target_net = CNN(state_dim, action_dim).to(self.device)

        for target_param, param in zip(self.target_net.parameters(), self.policy_net.parameters()):
            # 
            target_param.data.copy_(param.data)

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=cfg.lr)
        self.memory = ReplayBuffer(cfg.memory_capacity)

    def choose_action(self, state):
        """ epsilon-greedy 
        Returns:
            int: 
        """        
        # esilon 
        self.frame_idx += 1
        if random.random() > self.epsilon(self.frame_idx):
            with torch.no_grad():
                state = torch.tensor([state], device=self.device, dtype=torch.float32)
                # 
                q_values = self.policy_net(state)
                # 
                action = q_values.max(1)[1].item() 
        else:
            # 
            action = random.randrange(self.action_dim)
        return action

    def predict(self, state):
        """
        Returns:
            int: 
        """        
        with torch.no_grad():
            state = torch.tensor([state], device=self.device, dtype=torch.float32)
            q_values = self.policy_net(state)
            action = q_values.max(1)[1].item()
        return action

    def update(self):
        # 
        if len(self.memory) < self.batch_size: 
            return
        # (replay memory) (transition)
        state_batch, action_batch, reward_batch, next_state_batch, done_batch = \
            self.memory.sample(self.batch_size)
        # 
        state_batch = torch.tensor(
            state_batch, device=self.device, dtype=torch.float)

        action_batch = torch.tensor(action_batch, device=self.device).unsqueeze(1)  

        reward_batch = torch.tensor(
            reward_batch, device=self.device, dtype=torch.float)  

        next_state_batch = torch.tensor(
            next_state_batch, device=self.device, dtype=torch.float)

        done_batch = torch.tensor(np.float32(
            done_batch), device=self.device)

        # (s_t,a) Q(s_t, a)
        q_values = self.policy_net(state_batch).gather(dim=1, index=action_batch) 
        # (s_t_,a)
        next_q_values = self.target_net(next_state_batch).max(1)[0].detach() 

        # 
        expected_q_values = reward_batch + self.gamma * next_q_values * (1-done_batch)
        loss = nn.MSELoss()(q_values, expected_q_values.unsqueeze(1))  # 
        
        # 
        self.optimizer.zero_grad()  
        loss.backward()
        for param in self.policy_net.parameters():  # 
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step() 

    def save(self, path):
        torch.save(self.target_net.state_dict(), path+'dqn_checkpoint.pth')

    def load(self, path):
        self.target_net.load_state_dict(torch.load(path+'dqn_checkpoint.pth'))
        for target_param, param in zip(self.target_net.parameters(), self.policy_net.parameters()):
            param.data.copy_(target_param.data)