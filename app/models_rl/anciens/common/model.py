#!/usr/bin/env python
# coding=utf-8
'''
Author: John
Email: johnjim0816@gmail.com
Date: 2021-03-12 21:14:12
LastEditor: YangDing
LastEditTime: 2021-12-11
Discription: neural network models
'''
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

class MLP(nn.Module):
    def __init__(self, input_dim,output_dim,hidden_dim=128):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim) 
        self.fc2 = nn.Linear(hidden_dim,hidden_dim) 
        self.fc3 = nn.Linear(hidden_dim, output_dim) 
        
    def forward(self, x):
        
        x = F.relu(self.fc1(x)) 
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class CNN(nn.Module):   
    def __init__(self, state_dim, action_dim):
        # state_dim  (3, 32, 32)
        # action_dim  1024

        #assert state_dim[0] == 3 and state_dim[1] == state_dim[2] and \
        #    pow(state_dim[1], 2) == action_dim #, "message"

        # 
        super(CNN, self).__init__()

        self.network = nn.Sequential(
            #
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # 
            nn.Conv2d(16, 48, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            #  48 * (state_dim[1]/4) * (state_dim[1]/4) 
            # = 3 * state_dim[1]^2 
            nn.Flatten(),
            # 
            nn.Linear(3 * action_dim, 2 * action_dim),
            nn.ReLU(),
            nn.Linear(2 * action_dim, action_dim),
        )

        
    def forward(self, x):
        result = self.network(torch.tensor(x))
        return result


class Critic(nn.Module):
    def __init__(self, n_obs, output_dim, hidden_size, init_w=3e-3):
        super(Critic, self).__init__()
        
        self.linear1 = nn.Linear(n_obs + output_dim, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, 1)
        # 
        self.linear3.weight.data.uniform_(-init_w, init_w)
        self.linear3.bias.data.uniform_(-init_w, init_w)
        
    def forward(self, state, action):
        # 
        x = torch.cat([state, action], 1)
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = self.linear3(x)
        return x


class Actor(nn.Module):
    def __init__(self, n_obs, output_dim, hidden_size, init_w=3e-3):
        super(Actor, self).__init__()  
        self.linear1 = nn.Linear(n_obs, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, output_dim)
        
        self.linear3.weight.data.uniform_(-init_w, init_w)
        self.linear3.bias.data.uniform_(-init_w, init_w)
        
    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = torch.tanh(self.linear3(x))
        return x


class ActorCritic(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=256):
        super(ActorCritic, self).__init__()
        self.critic = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        self.actor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Softmax(dim=1),
        )
        
    def forward(self, x):
        value = self.critic(x)
        probs = self.actor(x)
        dist  = Categorical(probs)
        return dist, value