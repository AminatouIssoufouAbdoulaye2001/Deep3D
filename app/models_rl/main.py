import numpy as np
import pandas as pd
from article.articles import Articles
from carton.cartons import Cartons, create_bins
from environnement.env import Environment
from dqnet.model import QNetwork
import torch
import torch.optim as optim
import torch.nn as nn
from torch.optim.lr_scheduler import StepLR
import random
from tqdm import tqdm
import matplotlib.pyplot as plt
import argparse
import collections
import warnings

# Ignorer les avertissements "SettingWithCopyWarning"
warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description = 'Train or test neural net')
parser.add_argument('--train', dest = 'train', action = 'store_true', default = False)
parser.add_argument('--test', dest = 'test', action = 'store_true', default = True)



def select_action(model, env, state, eps, Q):
    
    #state = torch.Tensor(state)
    with torch.no_grad():
        values = model(torch.tensor(env.items_data(state), dtype=torch.float32))

    # select a random action wih probability eps
    if random.random() <= eps:
        n = len(env.available_cartons())
        action = np.random.randint(0, n)
    else:
        #action = values.argmax(0).item()
        action = np.argmax(Q[state])
        #np.argmax(values.cpu().numpy())

    
    return action
def select_action1(model, env, state, eps):
    with torch.no_grad():
        values = model(torch.tensor(env.items_data(state)))
    # select a random action wih probability eps
    if random.random() <= eps:
        n = len(env.available_cartons())
        action = np.random.randint(0, n)
        #action = np.random.choice(env.available_cartons())
    else:
        action = values.argmax(0).item()

    
    return action

def update_parameters(current_model, target_model):
    target_model.load_state_dict(current_model.state_dict())

def train_model(env, n_ep, epsilon = 0.05, alpha = 0.2, gamma = 0.9, lr = 0.1, max_it = 2000):

    Q = np.zeros((len(df_article), len(df_carton)))
    T = np.zeros((len(df_article), len(df_carton)))
    somme_rewards = []

    model = QNetwork(torch.tensor(5), torch.tensor(len(df_carton)))
    target = QNetwork(torch.tensor(5), torch.tensor(len(df_carton)))
    optimizer = optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    
    for ep in tqdm(range(n_ep)):
        r_article = []
        it = 0

        state = env.reset()
        done = False
        constraint = False
        action_contraint = 0

        while not done:
            
            if constraint:
                action = action_contraint
            else:
                action = select_action(model, env, state, epsilon, Q)
                
            next_state, reward, lost_space, box_volume, article_volume, done, info = env.step(action)
            
            if len(info)==0:
                T[state, action]+=1
                action_contraint = action
                constraint = True
            else : 
                constraint = False
                
            """
            q_values = model(torch.Tensor(state))
            next_q_values = model(torch.Tensor(next_state))
            next_q_state_values = target(torch.Tensor(next_state))
            
            q_value = q_values.max(0)#q_values.gather(1, action).squeeze(1)
            next_q_value = next_q_state_values.gather(1, torch.max(next_q_values, 1)[1].unsqueeze(1)).squeeze(1)
            expected_q_value = rewards + gamma * next_q_value * (1 - is_done)
            Q[env.return_id(state), action] += (alpha*(reward+gamma*np.max(Q[env.return_id(next_state)]) - Q[env.return_id(state), action]))*(1-done)
            loss = (q_value - expected_q_value.detach()).pow(2).mean()
            if done: r_article.append(reward)
            optim.zero_grad()
            loss.backward()
            optim.step()
            """
            target = reward
            Q[state, action] += alpha*(reward+gamma*np.max(Q[next_state]) - Q[state, action])
            if not done:
                #Q[state, action] += alpha*(reward+gamma*np.max(Q[next_state]) - Q[state, action])
                target = reward + gamma * np.max(Q[next_state])
            else: r_article.append(reward)
            
            
            state = next_state
            if it > max_it:
                break
            it+=1

            #"""
        somme_rewards.append(np.mean(r_article))
        
    return Q.argmax(1), somme_rewards

def train_model1(env, n_ep, epsilon=0.05, alpha=0.2, gamma=0.9, lr=0.1):
    """Trains the Q-learning agent for a specified number of episodes.

    Args:
        env (gym.Env): The environment to interact with.
        n_ep (int): The number of episodes to train for.
        epsilon (float, optional): The exploration rate. Defaults to 0.15.
        alpha (float, optional): The learning rate. Defaults to 0.2.
        gamma (float, optional): The discount factor. Defaults to 0.9.
        lr (float, optional): The learning rate for the optimizer. Defaults to 0.1.

    Returns:
        QNetwork: The trained Q-network model.
    """
    somme_rewards = []
    state_size = len(df_article)  # Assuming df_article defines state features
    action_size = len(df_carton)  # Assuming df_carton defines available actions

    model = QNetwork(torch.tensor(5), torch.tensor(action_size))
    Q_2 = QNetwork(torch.tensor(5), torch.tensor(action_size))

    #for param in Q_2.parameters():
    #    param.requires_grad = False
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = StepLR(optimizer, step_size=100, gamma=lr)
    loss_fn = nn.MSELoss()

    for ep in tqdm(range(n_ep)):
        r_episode = []
        state = env.reset()
        done = False

        while not done:
            action = select_action1(model, env, state, epsilon)

            next_state, reward, lost_space, box_volume, article_volume, done, info = env.step(action)

            q_value = model(torch.tensor(state).unsqueeze(0)).max(1)[0]  # Get Q-value for current state
            target_value = reward  # Initialize target value
            if not done: print("reward de ", env.return_id(next_state), " : ", reward)

            if not done:
                next_q_values = model(torch.tensor(next_state).unsqueeze(0))
                next_q_state_values = Q_2(torch.tensor(next_state).unsqueeze(0))
                next_q_value = next_q_state_values.gather(1, torch.max(next_q_values, 1)[1].unsqueeze(1)).squeeze(1)
                target_value += gamma * next_q_value
                #target_value += gamma * next_q_values.max(1)[0]  # Update target with future reward

            expected_q_value = target_value.detach()  # Detach target for stability

            # Update model (on-policy)
            loss = loss_fn(q_value, expected_q_value)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            state = next_state
            r_episode.append(reward)
        somme_rewards.append(np.mean(r_article))

    return model, somme_rewards

def evaluate(model, env):
    # Use the trained model to make decisions in the environment
    state = env.reset()
    done = False
    matching = []
    while not done:
        action = select_action(model, env, state, epsilon)  # Select action based on Q-network
        next_state, reward, _, _, _, done, _ = env.step(action)  # Take action and observe outcome
        # Perform any necessary actions based on the environment's response
        state = next_state  # Update current state
        if done:
            matching.append([state, action])

    return matching

def view(pred, df_article, df_carton): 

    if isinstance(pred, pd.DataFrame):
        res = pred.copy()
    else :
        res = pd.DataFrame(pred, columns = ["id_carton"])
        res["id_article"] = res.index
    
    df_article["id"] = df_article.index
    res = res.join(df_article.set_index('id'), on='id_article')
    res["article_volume"] = res['Longueur'] * res['Largeur']  * res['Hauteur']* res["Quantite"]
    res = res[["id_article", "id_carton", "article_volume", "Poids"]]
    res["cumul_volume"] = res.groupby("id_carton")["article_volume"].transform("sum")
    res["cumul_poids"] = res.groupby("id_carton")["Poids"].transform("sum")
    df_carton["id"] = df_carton.index
    res = res.join(df_carton.set_index('id'), on='id_carton')
    res["box_volume"] = res['Longueur'] * res['Largeur']  * res['Hauteur']
    
    # calcul des indicateurs 
    res["esp_inocc"] = np.round(100*(res["box_volume"] - res["cumul_volume"])/res["box_volume"],2)
    res["poids_inocc"] = np.round(100*(res["Poids_max"] - res["cumul_poids"])/res["Poids_max"],2)

    list_def = ["id_article","id_carton","box_volume","article_volume", "cumul_volume", "esp_inocc", "poids_inocc"]
    #list_def = ["id_article","id_carton", "esp_inocc", "poids_inocc"]
    print("Descrition du resultat - Emballages : \n",
    res[list_def])#res[["id_article","id_carton","box_volume", "article_volume", "esp_inocc"]].head())

# a = volume_article, b = poids article, df = cartons disponibles
def bp(a, b, df):
        # Calculate absolute differences and indicator values
        #df['diff'] = np.abs(df['v'] - float(a))
        df.loc[:, 'diff'] = np.abs(df['v'] - float(a))
        #df['indicator'] = (df['v']>a)*(df['Poids_max']>b)
        df.loc[:, 'indicator'] = (df['v'] > a) & (df['Poids_max'] > b)

        # Multiply absolute differences and indicators
        #df['diff_indicator'] = df['diff'] * df['indicator']
        df.loc[:, 'diff_indicator'] = df['diff'] * df['indicator']

        # Sort by diff_indicator and get the index of the minimum value
        df = df[df["indicator"]==1]["diff_indicator"]

        if df.empty: 
            return None
        return df.idxmin()

# test - test 
def test_model(df_article, df_carton):

    # calcul du volume total
    df_article["v"] = df_article['Longueur'] * df_article['Largeur']  * df_article['Hauteur']* df_article["Quantite"]
    df_carton["v"] = df_carton['Longueur'] * df_carton['Largeur']  * df_carton['Hauteur']

    # articles dans un seul carton
    a = df_article["v"].sum()
    b = df_article["Poids"].sum()
    #packed = bp(a,b, df_carton)
    #if not packed is None:
    #    print("tous les articles sont emballés dans le carton ", packed)
    #    return 0
    
    div1 = int(df_article.shape[0]/2)
    #div = alpha*n (n = len(df_article))
    print("div1 : ", div1)
    df1 = df_article.iloc[:div1].copy()
    df2 = df_article.iloc[div1:].copy()

    a1 = df1["v"].sum()
    b1 = df1["Poids"].sum()
    packed1 = bp(a1,b1, df_carton)
    if not packed1 is None:
        print("les articles ", list(range(div1)), " sont emballés dans le carton ", packed1)
    
        a2 = df2["v"].sum()
        b2 = df2["Poids"].sum()
        packed2 = bp(a2,b2, df_carton[df_carton.index != packed1])
        if not packed1 is None:
            print("les articles ", list(range(div1, len(df_article))), " sont emballés dans le carton ", packed2)

def test(df_article, df_carton, alpha = 0.25): 
    
    # alpha = [0, 1]
    # alpha == 0 : tous les articles dans un seul carton
    # alpha == 0.1 : on divise les articles en 2 groupes par exemple
    # alpha == 0.2 : on divise en 5 groupes
    # ...
    # alpha == 1 : article = un carton
    # Calcul du volume total des articles et des cartons
    df_article["v"] = df_article['Longueur'] * df_article['Largeur'] * df_article['Hauteur'] * df_article["Quantite"]
    df_carton["v"] = df_carton['Longueur'] * df_carton['Largeur'] * df_carton['Hauteur']

    used_cartons = []  # Liste pour stocker les cartons déjà utilisés
    results = []  # Liste pour stocker les résultats de l'emballage

    # Diviser les articles en groupes en fonction de alpha
    n = len(df_article)
    div = int((1-alpha) * n)
    if div ==0: div+=1
    done = True

    grouped_articles = []
    for i in range(0, n, div):
        grouped_articles.append(df_article.iloc[i:i+div].copy())

    group_results = []  # Liste pour stocker les résultats de chaque groupe
    for i, df_group in enumerate(grouped_articles):
        # Calcul du volume et du poids total du groupe d'articles
        a_group = df_group["v"].sum()
        b_group = df_group["Poids"].sum()

        # Recherche d'un carton pour emballer le groupe d'articles
        cartons_except_used = df_carton[~df_carton.index.isin(used_cartons)]
        
        packed_group = bp(a_group, b_group, cartons_except_used)

        if packed_group is not None:
            # Enregistrer le résultat du groupe
            group_results.append((list(df_group.index), packed_group))
            used_cartons.append(packed_group)
        else:
            print("Aucun carton disponible pour emballer les articles : ", list(df_group.index))
            done *= False
    # Enregistrer les résultats pour cette valeur d'alpha
    #results.append(group_results)

    return group_results, done


if __name__ == '__main__':


    #if pack=='__click__':

        # boucle pour df_article

        # boucle pour df_carton

        # res, done = test(df_article, df_carton)

        # res pour faire viz 
        # save in txt and read the txt in html
    
    args = parser.parse_args()

    if args.train:
        df_article = pd.read_csv("data/articles_data.csv")
        new_names = {'longueur': 'Longueur', 'largeur': 'Largeur',
        "hauteur": "Hauteur", "poids": "Poids", "quantite": "Quantite"}
        df_article = df_article.rename(columns=new_names)
        df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]
        print( "Nombre Articles : ", len(df_article))  
        
        
        #df_carton = create_bins(df_article)
        #df_carton = df_carton[0:5]

        #df_article = df_article[0:4]

        df_carton = pd.read_csv("data/conteneurs_data.csv")
        df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]
        #df_carton = df_carton[1:]
        print( "Nombre Cartons : ", len(df_carton)) 
        
        
        print("+++++++ ENVIRONNEMENT ++++++++++")
        # Initialiser l'env
        
        env = Environment( df_article , df_carton)
        #print("Env initial : ", env.reset())
        
        ## Appel à train et pred
        #pred = train_model(env, 10) # 10 = nb episodes
        trained_model, r = train_model(env, 100)
        #model, r = train_model1(env, 400)

        # Affichage des resultats
        view(trained_model, df_article, df_carton)
        #packer_method(df_carton, df_article)

        plt.plot(r)
        plt.ylabel("Espace occupe (en %)")
        plt.xlabel("Episode")
        plt.savefig('train1.png')
        plt.show()
        plt.close()
        

    else:#if args.test:
        #test_model(df_article, df_carton)
        #res, done = test(df_article, df_carton)
        N = 400
        #np.random.seed(2024)
        articles = Articles(N)
        df_article = articles.generate_dataframe()

        # articles du csv
        df_article = pd.read_csv("data/articles_data.csv")
        new_names = {'longueur': 'Longueur', 'largeur': 'Largeur',
        "hauteur": "Hauteur", "poids": "Poids", "quantite": "Quantite"}
        df_article = df_article.rename(columns=new_names)
        df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]

        
        #np.random.seed(5)
        cartons = Cartons(N) 
        df_carton = cartons.generate_dataframe()
        df_carton = create_bins(df_article)
        
        # conteneurs du csv
        df_carton = pd.read_csv("data/conteneurs_data.csv")
        df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max', 'Quantite']]

        
        done = True
        #alpha = 0.1
        
        for alpha in np.arange(0,1+0.1,0.1):
            #
            res, done = test(df_article, df_carton, alpha)
            #print("===================\n\n", res,"\n\n")
            if not done:print("alpha=",np.round(alpha,2), ",done=",done," Résultat : ", res)
        
            c1 = [] #[x[0] for x in res]
            c2 = [] #[x[1] for x in res]
            c3 = []
            
            # calculer les sorties que si tous les articles sont classés ou dernier élement de la boucle
            if (alpha==1.0) or done:
                print("value: ", np.round(alpha,2))
                for x in res:
                    for i in x[0]:
                        c1.append(i)
                        c2.append(x[1])
                        c3.append(x[0])

                # Création du DataFrame
                df = pd.DataFrame({'id_article': c1, 'id_carton': c2, 'pack_together': c3})
                break
            
        # résultat d'emballage
        print("Résultat d'emballage des articles")
        print(df)
        # Affichage des resultats
        view(df, df_article, df_carton)
    
        