import numpy as np
#import gym
from deepqnet import DeepQNetwork
import argparse
import matplotlib.pyplot as plt
#import pickle
#import gzip
np.set_printoptions(threshold=12)#np.inf)


parser = argparse.ArgumentParser(description = 'Train or test neural net')
parser.add_argument('--train', dest = 'train', action = 'store_true', default = False)
parser.add_argument('--test', dest = 'test', action = 'store_true', default = True)
args = parser.parse_args()

## Init the environment
def env_init():
    Q1 = 0
    Q2 = 0
    stat = 0
    return Q1, Q2, stat


## reward by step
step_set = []
reward_set = []

## for train part
if args.train:
    ## RL init
    RL = DeepQNetwork(n_actions = 2,
                n_features = 3,
                learning_rate = 0.01,
                e_greedy = 0.9,
                replace_target_iter = 100,
                memory_size = 2000,
                e_greedy_increment = 0.001)
    
    ## Environment init
    Q1, Q2, stat = env_init()
    for steps in range(2000): # 20000
        if Q1>10 or Q2>10:
            Q1, Q2, stat = env_init()
        if np.random.random()<0.25:
            Q1+= 1
        if np.random.random()<0.25:
            Q2+= 1
        obs = np.array([Q1, Q2, stat])

        ## Choose the action
        action = RL.choose_action(obs)
        if action == 0:  #change
            if stat == 0:
                stat = 2
            elif stat == 1:
                stat = 3
            elif stat == 2:
                stat = 1
                if Q2>0:
                    Q2-=1
            elif stat == 3:
                stat = 0
                if Q1>0:
                    Q1-=1
        elif action == 1:  #keep on
            if stat==0:
                if Q1>0:
                    Q1-=1
            elif stat==1:
                if Q2>0:
                    Q2-=1



        else:
            print("Action error!")
        reward = -(Q1**2+Q2**2)
        obs_=np.array([Q1,Q2,stat])
        RL.store_transition(obs,action,reward,obs_)

        ## Train the networks if step number > 200 
        if steps>200:
            RL.learn()
        if steps%50==0:
            print(reward)

        ## Save the reward at each step     
        reward_set.append(reward)
        step_set.append(steps)
        obs=obs_
    
    plt.plot(step_set,reward_set, color = 'red')
    plt.ylabel("Reward")
    plt.xlabel("Step")
    plt.savefig('save/train.png')
    RL.store()
    plt.show()
    RL.plot_cost()

## for test model
if args.test:
    RL = DeepQNetwork(n_actions=2,
                #n_features=env.observation_space.shape[0],
                n_features=3,
                learning_rate=0.01, e_greedy=1.,
                replace_target_iter=100, memory_size=2000,
                e_greedy_increment=None,)
    ## init reward per step
    step_set=[]
    reward_set=[]
    Q1,Q2,stat = env_init()
    RL.restore()
    for steps in range(1000):
        if Q1>10 or Q2>10:
            Q1,Q2,stat=env_init()
        if np.random.random()<0.25:
            Q1+=1
        if np.random.random()<0.25:
            Q2+=1
        obs=np.array([Q1,Q2,stat])
        action=RL.choose_action(obs)
        print(obs, action)
        if action ==0:  #change
            if stat==0:
                stat=2
            elif stat==1:
                stat=3
            elif stat==2:
                stat=1
                if Q2>0:
                    Q2-=1
            elif stat==3:
                stat=0
                if Q1>0:
                    Q1-=1
        elif action == 1:  #keep on
            if stat==0:
                if Q1>0:
                    Q1-=1
            elif stat==1:
                if Q2>0:
                    Q2-=1

        else:
            print("Action erronée !! ")
        reward = -(Q1**2+Q2**2)
        obs_=[Q1,Q2,stat]

        if steps%50==0:
            print(reward)
        
        obs=obs_
        steps+=1
        reward_set.append(reward)
        step_set.append(steps)
    
    # Graph for rewards by step
    plt.plot(step_set,reward_set)
    plt.ylabel("Reward")
    plt.xlabel("Step")
    plt.savefig('save/test.png')
    plt.show()
    

        
