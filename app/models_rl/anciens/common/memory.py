#!/usr/bin/env python
# coding=utf-8
'''
@Author: John
@Email: johnjim0816@gmail.com
@Date: 2020-06-10 15:27:16
@LastEditor: John
LastEditTime: 2021-09-15 14:52:37
@Discription: 
@Environment: python 3.7.7
'''
import random
class ReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity 
        self.buffer = [] 
        self.position = 0 
    
    def push(self, state, action, reward, next_state, done):

        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity 
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done =  zip(*batch) 
        return state, action, reward, next_state, done
    
    def __len__(self):
        return len(self.buffer)