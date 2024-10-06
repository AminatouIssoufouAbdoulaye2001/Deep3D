import random
from collections import deque
import numpy as np
import tensorflow as tf
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.optimizers import Adam
from time import time, sleep

class DQNAgent:
    def __init__(self, state_size, action_size, args):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=args.maxlen) #utilisée ici pour stocker les expériences de l'agent.
        self.gamma = args.gamma   # Facteur de réduction pour les récompenses futures (discount factor).
        self.epsilon = args.epsilon  # exploration rate 
        self.epoch = args.episode
        self.epsilon_min = args.epsilon_min
        self.epsilon_decay = args.epsilon_decay
        self.learning_rate = args.learning_rate
        self.model = self._build_model()
        self.loss_function = tf.keras.losses.Huber()  # Changed to Huber loss
        self.losses = []
        
    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    #Stock en mémoire les experience de l'agent sous forme de tuple. efface les ancienne experience en cas de memoire pleine
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    #choix du carton
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])
    #emballer tous les articles dans le meme carton
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
    #garde en  memoire la position de l'articles dans le carton etc...
    #il permet de modeliser x et y(carton de l'articles)
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        states, targets = [], []
        
        for state, action, reward, next_state, done in minibatch:
            target = self.model.predict(state)
            if done:
                target[0][action] = reward
            else:
                t = self.model.predict(next_state)[0]
                target[0][action] = reward + self.gamma * np.amax(t)
            
            states.append(state[0])
            targets.append(target[0])
        
        states = np.array(states)
        targets = np.array(targets)
        
        history = self.model.fit(states, targets, epochs=1, verbose=0)
        loss = history.history['loss'][0]
        self.losses.append(loss)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss

    def save_loss(self, path):
        np.save(path, self.losses)
        return self.losses
    def load(self, name):
        self.model = load_model(name)
    
    def save(self, name):
        self.model.save(name)

