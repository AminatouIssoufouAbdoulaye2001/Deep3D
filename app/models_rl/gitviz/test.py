import random
import numpy as np
from pack import *
from show import *
import time
import queue
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def visualize_packing(carton_df, article_df, save_path):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot each carton as a transparent box
    for _, carton in carton_df.iterrows():
        x_size = carton['Longueur']
        y_size = carton['Largeur']
        z_size = carton['Hauteur']
        ax.add_collection3d(Poly3DCollection([[(0, 0, 0), (x_size, 0, 0), 
                                               (x_size, y_size, 0), (0, y_size, 0)],
                                              [(0, 0, z_size), (x_size, 0, z_size),
                                               (x_size, y_size, z_size), (0, y_size, z_size)],
                                              [(0, 0, 0), (0, y_size, 0), 
                                               (0, y_size, z_size), (0, 0, z_size)],
                                              [(x_size, 0, 0), (x_size, y_size, 0), 
                                               (x_size, y_size, z_size), (x_size, 0, z_size)],
                                              [(0, 0, 0), (x_size, 0, 0), 
                                               (x_size, 0, z_size), (0, 0, z_size)],
                                              [(0, y_size, 0), (x_size, y_size, 0), 
                                               (x_size, y_size, z_size), (0, y_size, z_size)]], 
                                              facecolors='cyan', linewidths=1, edgecolors='r', alpha=.25))
    
    # Plot each article
    for _, article in article_df.iterrows():
        x_size = article['Longueur']
        y_size = article['Largeur']
        z_size = article['Hauteur']
        
        # Place the article randomly within its carton
        carton = carton_df[carton_df['id_carton'] == article['id_carton']].iloc[0]
        x_pos = np.random.uniform(0, carton['Longueur'] - x_size)
        y_pos = np.random.uniform(0, carton['Largeur'] - y_size)
        z_pos = np.random.uniform(0, carton['Hauteur'] - z_size)
        
        vertices = np.array([[
            (x_pos, y_pos, z_pos), (x_pos + x_size, y_pos, z_pos), 
            (x_pos + x_size, y_pos + y_size, z_pos), (x_pos, y_pos + y_size, z_pos),
            (x_pos, y_pos, z_pos + z_size), (x_pos + x_size, y_pos, z_pos + z_size),
            (x_pos + x_size, y_pos + y_size, z_pos + z_size), (x_pos, y_pos + y_size, z_pos + z_size)
        ]])
        
        ax.add_collection3d(Poly3DCollection(vertices, linewidths=1, edgecolors='k', alpha=.5))

    ax.set_xlabel('Longueur')
    ax.set_ylabel('Largeur')
    ax.set_zlabel('Hauteur')
    ax.set_title('Disposition des articles dans les cartons')
    
    plt.savefig(save_path)
    plt.show()


def getSurfaceItem(xSize, ySize, zSize):

    cube = np.ones((xSize, ySize, zSize))
    # 将内部全部置为0，只保留表面
    cube[1: xSize-1, 1: ySize-1, 1: zSize-1] = 0

    return Item(cube)

def Task1():
    box_size = (30, 30, 30)
  
    # 空心的，只保留表面，计算速度快
    items = [getSurfaceItem(10, 9, 12),
             getSurfaceItem(7, 6, 10),
             getSurfaceItem(8, 10, 9), 
             getSurfaceItem(10, 7, 8),
             getSurfaceItem(9, 8, 5),
             getSurfaceItem(8, 5, 4),
            ]

    problem = PackingProblem(box_size, items)

    # problem.pack_all_items()
    display = Display(box_size)
    
    for idx in range(len(items)):
        problem.autopack_oneitem(idx)   
        display.show3d(problem.container.geometry)
        # time.sleep(0.5)
        #plt.pause(0.5)
        plt.savefig('test.png')

def Task(box_size, items, save_path):
    problem = PackingProblem(box_size, items)
    display = Display(box_size)
    
    for idx in range(len(items)):
        try:
            problem.autopack_oneitem(idx)
        except AssertionError as e:
            print(f"Erreur lors de l'emballage de l'article {idx}: {str(e)}")
            continue  # Passe à l'article suivant
        
        display.show3d(problem.container.geometry)
        plt.savefig(save_path)
        plt.clf()  # Clear the figure for the next save

def Task2(box_size, items, save_path):
    problem = PackingProblem(box_size, items)
    display = Display(box_size)
    
    for idx in range(len(items)):
        problem.autopack_oneitem(idx)
        display.show3d(problem.container.geometry)
        plt.savefig(save_path)
        plt.clf()  # Clear the figure for the next save

def pack_viz1(res, article_df, carton_df):
    # Dictionnaire pour stocker les articles groupés par carton_id
    grouped_articles = res.groupby('id_carton')['id_article'].apply(list).to_dict()

    for carton_id, article_ids in grouped_articles.items():
        # Filtrer les articles par leurs IDs
        articles = article_df[article_df['id_article'].isin(article_ids)]
        
        # Créer les objets Item pour chaque article
        items = [getSurfaceItem(int(row['Longueur']), int(row['Largeur']), int(row['Hauteur'])) for _, row in articles.iterrows()]
        
        # Définir la taille de la boîte (carton)
        carton = carton_df[carton_df['id_carton'] == carton_id].iloc[0]
        box_size = (int(carton['Longueur']), int(carton['Largeur']), int(carton['Hauteur']))
        
        # Appeler la fonction Task pour le groupe carton-articles
        save_path = f'save/carton_{carton_id}.png'
        Task(box_size, items, save_path)

def pack_viz(res, article_df, carton_df):
    # Dictionnaire pour stocker les articles groupés par carton_id
    grouped_articles = res.groupby('id_carton')['id_article'].apply(list).to_dict()

    for carton_id, article_ids in grouped_articles.items():
        # Filtrer les articles par leurs IDs
        print("carton id : ", carton_id)
        articles = article_df[article_df['id_article'].isin(article_ids)]
        print(articles)
        print(article_ids)
        articles['id_carton'] = int(carton_id)
        print(carton_id)
        print(carton_df)
        carton = carton_df[carton_df['id_carton'] == carton_id]
        
        # Appeler la fonction Task pour le groupe carton-articles
        save_path = f'save/carton_{carton_id}.png'
        visualize_packing(carton, articles, save_path)


if __name__ == "__main__":

    Task1()