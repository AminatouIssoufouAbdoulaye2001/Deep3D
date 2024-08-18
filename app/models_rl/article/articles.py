import numpy as np
import pandas as pd 


class Articles:
    def __init__(self, N):
        self.N = N
        self.df = self.generate_dataframe()

    def generate_dataframe(self):
        data = {
            'Longueur': np.round(np.random.uniform(1, 100, self.N),0),
            'Largeur': np.round(np.random.uniform(1, 100, self.N),0),
            'Hauteur': np.round(np.random.uniform(1, 100, self.N),0),
            'Fragile': np.random.choice([True, False], self.N),
            'Poids': np.round(np.random.uniform(1, 10, self.N),0),
            'Quantite': np.random.randint(1, 20, self.N)
        }
        
        # Filtrer les données p

        df = pd.DataFrame(data)
        df = df[df['Longueur'] > df['Largeur']]
        df = df[df['Quantite'] > 0]
        df.reset_index(drop=True, inplace=True)

        return df
    def get_volume(self):
        return self.df['Longueur'] * self.df['Largeur'] * self.df['Hauteur']
    
    def get_total_weights(self):
        return self.df['Poids'] * self.df['Quantite']