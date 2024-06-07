from app.models_rl.main_vf import *
import warnings
from time import sleep, time

parser = argparse.ArgumentParser(description = 'Train or test neural net')
parser.add_argument('--train', dest = 'train', action = 'store_true', default = False)
parser.add_argument('--test', dest = 'test', action = 'store_true', default = True)
parser.add_argument('--maxlen', type=int, default=2000, help='Max timesteps')
parser.add_argument('--gamma', type=float, default=0.90, help='Max timesteps')
parser.add_argument('--epsilon', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--epsilon_min', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--epsilon_decay', type=float, default= 0.995, help='Max timesteps')
parser.add_argument('--learning_rate', type=float, default=0.01, help='Max timesteps')
parser.add_argument('--episodes', type=int, default=300, help='Max timesteps')
parser.add_argument('--tmax', type=int, default=3000, help='Max timesteps')
parser.add_argument('--model_used', dest = 'model_used', action = 'store_true', default = False)


args = parser.parse_args()


def model_pack_articles(df_article, model_used=args.model_used):

    df_article = pd.DataFrame(df_article)
    df_article["Longueur"] = df_article['longueur']
    df_article["Largeur"] = df_article['largeur']
    df_article["Hauteur"] = df_article['hauteur']
    df_article["Poids"] = df_article['poids']
    df_article["Quantite"] = df_article['quantite']
    df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]

    df_carton = pd.read_csv("app/models_rl/data/conteneurs_data.csv")
    df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]
    ## BIN PACK
    print("dataFrame avant model")
    print(df_article)
    #sleep(100000)
    if model_used :
        print("+++++++ MODEL ++++++++++")
        env = Environment( df_article , df_carton)

        state_size = len(env.items_data(0))  #env.get_state_size()
        action_size = len(df_carton)
        agent = DQNAgent(state_size, action_size, args)

        #agent.load("save/model.h5")

        pred = evaluate(env, agent, state_size)
        #print("\n\nres : ", pred)

        return view(pred, df_article, df_carton)
    else :
        bin = Bin(df_article, df_carton)
        return bin.pack()

