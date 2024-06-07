import random
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import collections
import warnings
from environnement.env import Environment
from dqnet.agent import DQNAgent
import tensorflow as tf
import numpy as np
from time import time as t
from viz import *
# Ignorer les avertissements "SettingWithCopyWarning"
warnings.filterwarnings('ignore')


parser = argparse.ArgumentParser(description = 'Train or test neural net')
parser.add_argument('--train', dest = 'train', action = 'store_true', default = False)
parser.add_argument('--test', dest = 'test', action = 'store_true', default = True)
parser.add_argument('--maxlen', type=int, default=2000, help='Max timesteps')
parser.add_argument('--gamma', type=float, default=0.90, help='Max timesteps')
parser.add_argument('--epsilon', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--epsilon_min', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--epsilon_decay', type=float, default= 0.995, help='Max timesteps')
parser.add_argument('--learning_rate', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--episodes', type=int, default=2, help='Max timesteps')
parser.add_argument('--episode', type=int, default=5, help='Max timesteps')
parser.add_argument('--tmax', type=int, default=3000, help='Max timesteps')
parser.add_argument('--nb_article', type=int, default=4, help='Max timesteps')



def train(env, agent, action_size, episodes = 20, batch_size =32, plot=True):

    state_size = state_size = len(env.items_data(0))  #env.get_state_size()
    #action_size = len(cartons_df)
    scores = []
    times = []
    for e in range(episodes):
        state = env.reset()
        val_state = env.items_data(state)
        val_state = tf.convert_to_tensor(val_state, dtype=tf.float32) 
        val_state = np.reshape(val_state, [1, state_size])
        done = False
        
        constraint = False
        action_contraint = 0
        start = t()
        score = []
        print("ietération: ", e)
        while not done:
            if constraint:
                action = action_contraint
            else:
                action = agent.act(val_state)
            
            print("action en cours: ", action)
            print("state : " , state)
            next_state, reward, lost_space, box_volume, article_volume, done, info = env.step(action)
            print("next_state : " , next_state)
            print("+++++++++++++++++++++++++++")
            
            if len(info)==0:
                action_contraint = action
                constraint = True
                score.append(reward)
            else : 
                constraint = False
            
            val_next_state = env.items_data(next_state)
            val_next_state = tf.convert_to_tensor(val_next_state, dtype=tf.float32)
            val_next_state = np.reshape(val_next_state, [1, state_size])
            
            agent.remember(val_state, action, reward, val_next_state, done)
            state = next_state
            val_state = val_next_state
            if done:
                print(f"Episode: {e}/{episodes}, Score: {time}, e: {agent.epsilon:.2}")
                break
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
            
        scores.append(np.mean(score))
        times.append(t()-start)
        if e >= 20 and e % 5 :
            savepath = "save/model_" + str (e) + "nb.h5" 
            agent.save(savepath)
    agent.save("save/model.h5") 
    # Afficher les graphiques de performance
    if plot:
        plt.figure(figsize=(12, 6))
        plt.plot(scores)
        plt.xlabel('Episodes')
        plt.ylabel('Reward')
        plt.title('Espace occupé par episode')
        plt.savefig('save/train.png')
        #plt.show()
        
        plt.figure(figsize=(12, 6))
        plt.plot(times)
        plt.xlabel('Episodes')
        plt.ylabel('Time (s)')
        plt.title('Temps par episode')
        plt.savefig('save/train_times.png')
        #plt.show()


def evaluate(env, agent, state_size):
    # Use the trained model to make decisions in the environment
    state = env.reset()
    val_state = env.items_data(state)
    val_state = tf.convert_to_tensor(val_state, dtype=tf.float32)
    val_state = np.reshape(val_state, [1, state_size])
    done = False
    constraint = False
    action_contraint = 0
    matching = []
    tested_actions = set()
    
    while not done:
        if constraint:
            action = action_contraint
        else:
            #action = agent.act1(val_state, tested_actions)
            action = agent.act(val_state)

        next_state, reward, lost_space, box_volume, article_volume, done, info = env.step(action)
        
        if next_state==state:
            tested_actions.add(action)
        if len(info)==0:
            
            action_contraint = action
            constraint = True
            matching.append([state, action])
            tested_actions = set()
        else : 
            constraint = False
        
        state = next_state  # Update current state

    return pd.DataFrame(matching, columns = ['id_article', 'id_carton'])


def test(env, agent, action_size, episodes = 10, plot = True):
    state_size = len(env.items_data(0))
    #action_size = len(test_cartons_df)
    Q = np.zeros((state_size, action_size))

    # Tester l'agent avec les données de test
    scores = []
    times = []

    for e in range(episodes):
        start = t()
        state = env.reset()
        val_state = env.items_data(state)
        val_state = tf.convert_to_tensor(val_state, dtype=tf.float32)
        val_state = np.reshape(val_state, [1, state_size])
        score = []

        done = False
        constraint = False
        action_contraint = 0

        while not done:
            if constraint:
                action = action_contraint
            else:
                action = agent.act(val_state)
            
            next_state, reward, lost_space, box_volume, article_volume, done, info = env.step(action)
            
            if len(info)==0:
                Q[state, action]+=1
                action_contraint = action
                score.append(reward)
                constraint = True
            else : 
                constraint = False
            
            if not done:
                next_val_state = env.items_data(next_state)
                next_val_state = tf.convert_to_tensor(next_val_state, dtype=tf.float32)
                next_val_state = np.reshape(next_val_state, [1, state_size])
                val_state = next_val_state
            else:
                scores.append(np.mean(score))
                print(f"Episode: {e}/{episodes}, Score: {score}")
                break
        times.append(t()-start)

    # Calculer la moyenne des scores
    average_score = np.mean(scores)
    print(f"\n\nAverage Score over {episodes} episodes: {average_score}")
    
    
    # Afficher les graphiques de performance
    if plot:
        plt.figure(figsize=(12, 6))
        plt.plot(scores)
        plt.xlabel('Episodes')
        plt.ylabel('Reward')
        plt.title('Espace occupé par episode')
        plt.savefig('save/test.png')
        #plt.show()
        
        plt.figure(figsize=(12, 6))
        plt.plot(times)
        plt.xlabel('Episodes')
        plt.ylabel('Time (s)')
        plt.title('Temps par episode')
        plt.savefig('save/times.png')
        #plt.show()

    
    return Q.argmax(1)


if __name__ == '__main__':

    args = parser.parse_args()

    if args.train:
        df_article = pd.read_csv("app/models_rl/data/articles_data.csv")
        new_names = {'longueur': 'Longueur', 'largeur': 'Largeur',
        "hauteur": "Hauteur", "poids": "Poids", "quantite": "Quantite"}
        df_article = df_article.rename(columns=new_names)
        df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]
        print( "Nombre Articles : ", len(df_article)) 
        df_article = df_article[:args.nb_article]
        df_carton = pd.read_csv("app/models_rl/data/conteneurs_data.csv")
        df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]
        #df_carton = df_carton[1:]
        print( "Nombre Cartons : ", len(df_carton)) 


        # Initialiser l'env
        print("+++++++ ENVIRONNEMENT ++++++++++")
        env = Environment( df_article , df_carton)

        state_size = state_size = len(env.items_data(0))  #env.get_state_size()
        action_size = len(df_carton)
        agent = DQNAgent(state_size, action_size, args)

        train(env, agent, action_size, episodes=args.episodes)
    
    if args.test or not args.train:
        print("=============== Test modèle : ====================\n\n")
        df_article = pd.read_csv("app/models_rl/data/articles_data.csv")
        new_names = {'longueur': 'Longueur', 'largeur': 'Largeur',
        "hauteur": "Hauteur", "poids": "Poids", "quantite": "Quantite"}
        df_article = df_article.rename(columns=new_names)
        df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]
        df_article = df_article[:4]
        print( "Nombre Articles : ", len(df_article)) 

        df_carton = pd.read_csv("app/models_rl/data/conteneurs_data.csv")
        df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]
        #df_carton = df_carton[1:]
        print( "Nombre Cartons : ", len(df_carton)) 


        # Initialiser l'env
        print("+++++++ ENVIRONNEMENT ++++++++++")
        env = Environment( df_article , df_carton)

        state_size = len(env.items_data(0))  #env.get_state_size()
        action_size = len(df_carton)
        agent = DQNAgent(state_size, action_size, args)
        #agent.load("save/model.h5")

        #res = test(env, agent, action_size, 20)
        #print("id_carton : ", res)

        ## Eval model
        pred = evaluate(env, agent, state_size)
        #print("\n\nres : ", pred)

        view(pred, df_article, df_carton)

        ## BIN PACK
        bin = Bin(df_article, df_carton)
        bin.pack()


