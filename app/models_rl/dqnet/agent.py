import random
from collections import deque
import numpy as np
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from time import time, sleep

class DQNAgent:
    def __init__(self, state_size, action_size,args):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=args.maxlen)
        self.gamma = args.gamma   # discount rate
        self.epsilon = args.epsilon  # exploration rate
        self.epoch = args.episode
        self.epsilon_min = args.epsilon_min
        self.epsilon_decay = args.epsilon_decay
        self.learning_rate = args.learning_rate
        self.model = self._build_model()
    
    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])
    
    def act1(self, state, ma_liste):
        
        if ma_liste:#np.random.rand() <= self.epsilon:
            return random.choice(ma_liste)
            #possible_actions = list(set(range(self.action_size)) - set(excluded_actions))
            """
            if possible_actions:
                return random.choice(possible_actions)
            else:
                return random.randrange(self.action_size)
            """
        act_values = self.model.predict(state)
        sorted_actions = np.argsort(act_values[0])[::-1]  # Sort actions by predicted value (descending)
        for action in sorted_actions:
            if action in ma_liste:
                return action
        return sorted_actions[0]  # Return the best available action if all preferred actions are excluded
    
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=1)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def load(self, name):
        self.model.load_weights(name)
    
    def save(self, name):
        self.model.save_weights(name)

