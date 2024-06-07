import torch
import torch.nn as nn
import torch.optim as optim

class QNetwork(nn.Module):
  def __init__(self, state_size, action_size):
    super().__init__()
    self.fc1 = nn.Linear(state_size, 64)
    self.fc2 = nn.Linear(64, 64)
    self.fc3 = nn.Linear(64, action_size)

  def forward(self, x):
    x = nn.ReLU()(self.fc1(x))
    x = nn.ReLU()(self.fc2(x))
    return self.fc3(x)