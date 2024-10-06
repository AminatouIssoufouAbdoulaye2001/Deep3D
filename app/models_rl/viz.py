import numpy as np
import pandas as pd
import plotly.graph_objects as go
import random
import os
from itertools import permutations, product
import vtk
import concurrent.futures


def view(pred, df_article, df_carton): 
    # Vérifier si pred est un DataFrame
    if isinstance(pred, pd.DataFrame):
        res = pred.copy()
    else:
        res = pd.DataFrame(pred, columns=["id_carton"])
        res["id_article"] = res.index
    
    df_article["id"] = df_article.index
    res = res.join(df_article.set_index('id'), on='id_article')
    res["article_volume"] = res['Longueur'] * res['Largeur'] * res['Hauteur'] * res["Quantite"]
    res["Poids_Qte"] = res["Poids"] * res["Quantite"]

    res["cumul_volume"] = res.groupby("id_carton")["article_volume"].transform("sum")
    res["cumul_poids"] = res.groupby("id_carton")["Poids_Qte"].transform("sum")
    df_carton["id"] = df_carton.index
    res = res.rename(columns = {
        'Longueur': 'Longueur Article (cm)',
        'Largeur': 'Largeur Article (cm)',
        'Hauteur': 'Hauteur Article (cm)',
        'Poids': 'Poids Article (kg)',
        'Quantite': 'Quantite Article',
        'v': 'v_last'
    })
    res = res.join(df_carton.set_index('id'), on='id_carton')
    res["box_volume"] = res['Longueur'] * res['Largeur'] * res['Hauteur']
     # Calcul des indicateurs 
    res["esp_inocc"] = np.round(100 * (res["box_volume"] - res["cumul_volume"]) / res["box_volume"], 2)
    res["poids_inocc"] = np.round(100 * (res["Poids_max"] - res["cumul_poids"]) / res["Poids_max"], 2)

    res = res.rename(columns = {
        'Longueur': 'Longueur Carton (cm)',
        'Largeur': 'Largeur Carton (cm)',
        'Hauteur': 'Hauteur Carton (cm)',
        'Poids_max': 'Poids_max Carton (kg)',
        'Quantite': 'Quantite Carton',
    })

    #list_def = ["id_article", "id_carton", "box_volume", "article_volume", "cumul_volume", "esp_inocc", "cumul_poids", "Poids_max", "poids_inocc"]
    
    #res = res.drop('v', axis =0)#[list_def]
    
    # Décommenter les lignes ci-dessous si vous souhaitez renommer les colonnes
    
    
    res = res.rename(columns={
        'id_article': 'ID Article',
        'id_carton': 'ID Carton',
        'box_volume': "Volume Carton",
        "article_volume": "Volume Article",
        "cumul_volume": "Volume Articles",
        "esp_inocc": "Espace inoccupé",
        "cumul_poids": "Poids Articles",
        "Poids_max": "Poids Max",
        "poids_inocc": "Poids inoccupé"
    })
    return res

def visualize_packing1(df):
    list_carton = list(pd.unique(df['ID Carton']))
    results = []
    for id_carton in list_carton:
        df_temp = df[df['ID Carton'] == id_carton].copy()
        df_temp['Volume Article (cm^3)'] = df_temp['Longueur Article (cm)'] * df_temp['Largeur Article (cm)'] * df_temp['Hauteur Article (cm)']
        df_temp = df_temp.sort_values(by='Volume Article (cm^3)', ascending=False)
        result = visualize_packing(df_temp, id_carton)
        results.append(result)
    return results

def pack_articles(articles, carton_length, carton_width, carton_height):
    def can_place(x, y, z, dx, dy, dz, placed):
        if x + dx > carton_length or y + dy > carton_width or z + dz > carton_height:
            return False
        for p in placed:
            px, py, pz, pdx, pdy, pdz = p['position']
            if (x < px + pdx and x + dx > px and
                y < py + pdy and y + dy > py and
                z < pz + pdz and z + dz > pz):
                return False
        return True

    def find_best_position(article, placed, empty_spaces):
        best_position = None
        best_space_index = -1
        min_wasted_space = float('inf')
        
        rotations = list(permutations(article))

        for space_index, (sx, sy, sz, sdx, sdy, sdz) in enumerate(empty_spaces):
            for rotation in rotations:
                dx, dy, dz = rotation
                if dx <= sdx and dy <= sdy and dz <= sdz:
                    wasted_space = (sdx * sdy * sdz) - (dx * dy * dz)
                    if wasted_space < min_wasted_space and can_place(sx, sy, sz, dx, dy, dz, placed):
                        best_position = (sx, sy, sz, dx, dy, dz)
                        best_space_index = space_index
                        min_wasted_space = wasted_space

        return best_position, best_space_index

    def update_empty_spaces(empty_spaces, used_space, best_space_index):
        x, y, z, dx, dy, dz = used_space
        sx, sy, sz, sdx, sdy, sdz = empty_spaces[best_space_index]
        
        new_spaces = []
        if x + dx < sx + sdx:
            new_spaces.append((x + dx, sy, sz, sdx - dx, sdy, sdz))
        if y + dy < sy + sdy:
            new_spaces.append((sx, y + dy, sz, dx, sdy - dy, sdz))
        if z + dz < sz + sdz:
            new_spaces.append((sx, sy, z + dz, dx, dy, sdz - dz))
        
        empty_spaces = empty_spaces[:best_space_index] + empty_spaces[best_space_index+1:] + new_spaces
        return empty_spaces

    placed = []
    empty_spaces = [(0, 0, 0, carton_length, carton_width, carton_height)]
    
    for article in sorted(articles, key=lambda a: a[0]*a[1]*a[2], reverse=True):
        position, space_index = find_best_position(article, placed, empty_spaces)
        if position:
            placed.append({'dimensions': article, 'position': position})
            empty_spaces = update_empty_spaces(empty_spaces, position, space_index)

    volume_utilisé = sum(a['dimensions'][0] * a['dimensions'][1] * a['dimensions'][2] for a in placed) / (carton_length * carton_width * carton_height)
    return placed, volume_utilisé


def draw_parallelepiped(x, y, z, dx, dy, dz, color):
    return go.Mesh3d(
        x=[x, x, x+dx, x+dx, x, x, x+dx, x+dx],
        y=[y, y+dy, y+dy, y, y, y+dy, y+dy, y],
        z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color,
        opacity=1,  # Réduire légèrement l'opacité pour améliorer les performances
        flatshading=True  # Utiliser le flat shading pour un rendu plus rapide
    )

def random_color():
    return f'rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})'

def process_orientation(args):
    articles, orientation = args
    placed_articles, volume_utilisé = pack_articles(articles, *orientation)
    return placed_articles, volume_utilisé, orientation

def visualize_packing(df, id_carton):
    carton_dims = df[['Longueur Carton (cm)', 'Largeur Carton (cm)', 'Hauteur Carton (cm)']].iloc[0].tolist()
    nb_articles = len(df)
    articles = list(df[['Longueur Article (cm)', 'Largeur Article (cm)', 'Hauteur Article (cm)']].itertuples(index=False, name=None))
    
    carton_orientations = list(permutations(carton_dims))
    best_orientation = None
    best_volume_utilisé = 0
    best_placed_articles = []
    
    for orientation in carton_orientations:
        placed_articles, volume_utilisé = pack_articles(articles, *orientation)
        if len(placed_articles) > len(best_placed_articles) or (len(placed_articles) == len(best_placed_articles) and volume_utilisé > best_volume_utilisé):
            best_orientation = orientation
            best_volume_utilisé = volume_utilisé
            best_placed_articles = placed_articles
    
    carton_length, carton_width, carton_height = best_orientation
    
    fig = go.Figure()
    fig.add_trace(draw_parallelepiped(0, 0, 0, carton_length, carton_width, carton_height, 'rgba(200, 200, 200, 0.1)'))

    placed_articles_count = 0
    for i, article in enumerate(articles):
        if placed_articles_count < len(best_placed_articles) and article == best_placed_articles[placed_articles_count]['dimensions']:
            x, y, z, dx, dy, dz = best_placed_articles[placed_articles_count]['position']
            fig.add_trace(draw_parallelepiped(x, y, z, dx, dy, dz, random_color()))
            placed_articles_count += 1
        else:
            print(f"Article {i+1} ne peut pas être emballé.")

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, carton_length], showticklabels=False, title=''),
            yaxis=dict(range=[0, carton_width], showticklabels=False, title=''),
            zaxis=dict(range=[0, carton_height], showticklabels=False, title=''),
            aspectmode='data'
        ),
        title=f'Visualisation de l\'emballage dans le carton {id_carton} (Articles placés: {placed_articles_count}/{nb_articles})',
        margin=dict(r=20, l=10, b=10, t=40),
        annotations=[
            dict(
                x=0.05,
                y=0.95,
                xref='paper',
                yref='paper',
                text=f'Volume utilisé: {best_volume_utilisé:.2%}',
                showarrow=False,
            )
        ]
    )

    fig.update_layout(scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)))
    fig.write_html(f"app/static/images/images_emballage/viz_carton{id_carton}.html")

    return {
        'carton_id': id_carton,
        'carton_dimensions': best_orientation,
        'articles_placés': placed_articles_count,
        'total_articles': nb_articles,
        'volume_utilisé': best_volume_utilisé
    }
# Exemple d'utilisation avec un DataFrame (df)
# visualize_packing_vtk(df, id_carton=1)



class Bin:

    def __init__(self, df_article, df_carton):
        self.alpha = 0.25
        self.df_article = df_article
        self.df_carton = df_carton
        self.df_article["v"] = df_article['Longueur'] * df_article['Largeur'] * df_article['Hauteur']
        self.df_carton["v"] = df_carton['Longueur'] * df_carton['Largeur'] * df_carton['Hauteur']

    @staticmethod
    def median_index(values):
        sorted_indices = np.argsort(values)
        median_idx = len(sorted_indices) // 2
        return sorted_indices[median_idx]

    @staticmethod
    def bp(a_dims, a_weight, df_carton):
        # a_dims is a sorted array of dimensions [Longueur, Largeur, Hauteur]
        a_dims = sorted(a_dims)

        def calculate_diff(carton):
            c_dims = sorted([carton['Longueur'], carton['Largeur'], carton['Hauteur']])
            # Calculate differences and handle negative differences
            diffs = [max(c_dims[i] - a_dims[i], 0) for i in range(len(a_dims))]
            result = np.array(diffs)
            return np.prod(result)

        df_carton['fits'] = df_carton.apply(
            lambda carton: all(np.array(sorted([carton['Longueur'], carton['Largeur'], carton['Hauteur']])) >= np.array(a_dims)) 
                           and carton['Poids_max'] >= a_weight, axis=1)

        df_carton['diff_indicator'] = df_carton.apply(lambda carton: calculate_diff(carton) if carton['fits'] else np.inf, axis=1)

        # Filter by indicator and get the index of the minimum diff_indicator
        filtered_df = df_carton[df_carton["fits"] == True]
        if filtered_df.empty:
            return None
            
        return filtered_df['diff_indicator'].idxmin()
    
    @staticmethod
    def bp1(a, b, df):
        # Calculate absolute differences and indicator values
        df['diff'] = np.abs(df['v'] - float(a))
        df['indicator'] = (df['v'] > a) & (df['Poids_max'] > b)

        # Multiply absolute differences and indicators
        df['diff_indicator'] = df['diff'] * df['indicator']

        # Filter by indicator and get the index of the minimum diff_indicator
        filtered_df = df[df["indicator"] == 1]
        if filtered_df.empty:
            return None
        return filtered_df['diff_indicator'].idxmin()
    
    @staticmethod
    def cumul_articles(df_group):
        # Initialize the total dimensions
        total_length, total_width, total_height = 0, 0, 0

        for index, row in df_group.iterrows():
            current_dims = sorted([row['Longueur'], row['Largeur'], row['Hauteur']])
            # Accumulate dimensions
            total_length += current_dims[0]
            total_width = max(total_width, current_dims[1])
            total_height = max(total_height, current_dims[2])

        # Return the combined dimensions in sorted order
        return sorted([total_length, total_width, total_height], reverse=True)

    @staticmethod
    def put2(df_article, df_carton, alpha=0.25):
        used_cartons = []  # List to store used cartons
        group_results = []  # List to store the results for each group

        # Create random groups of articles based on alpha
        n = len(df_article)
        div = max(int((1 - alpha) * n), 1)

        article_ids = df_article.index.tolist()
        grouped_articles = []

        # Group articles by dividing the DataFrame into chunks
        for i in range(0, n, div):
            grouped_articles.append(df_article.iloc[i:i+div].copy())
            
        for df_group in grouped_articles:
            # Calculate the total dimensions and weight for the group of articles
            print(" shape df_group : ", df_group.columns)
            a_dims = df_group["v"].sum() #Bin.cumul_articles(df_group)
            a_weight = df_group["Poids"].sum()

            # Search for a carton to pack the group of articles
            cartons_except_used = df_carton[~df_carton.index.isin(used_cartons)]
            #print("Dimensions combinees : ", a_dims)
            #print("Dimensions cartons : ", cartons_except_used)
            #print("===================\n\n")
            #print(ddss)
            packed_group = Bin.bp1(a_dims, a_weight, cartons_except_used)

            if packed_group is not None:
                # Record the result for the group
                group_results.append((list(df_group.index), packed_group))
                used_cartons.append(packed_group)
            else:
                return group_results, False  # Stop if no suitable carton is found

        return group_results, True

    def pack(self):
        df_article = self.df_article
        df_carton = self.df_carton

        for alpha in np.arange(0, 1.1, 0.1):
            res, done = Bin.put2(df_article, df_carton, alpha)
            if done or alpha == 1.0:
                c1 = []  # Article IDs
                c2 = []  # Carton IDs
                c3 = []  # Group of articles packed together

                for x in res:
                    for i in x[0]:
                        c1.append(i)
                        c2.append(x[1])
                        c3.append(x[0])

                # Create the resulting DataFrame
                df = pd.DataFrame({'id_article': c1, 'id_carton': c2, 'pack_together': c3})
                break
        return view(df, df_article, df_carton)