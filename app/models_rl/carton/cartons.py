import numpy as np
import pandas as pd 


class Cartons:
    def __init__(self, N):
        self.N = N
        self.df = self.generate_dataframe()

    def generate_dataframe(self):
        data = {
            'Longueur': np.round(np.random.uniform(10, 100, self.N),0),
            'Largeur': np.round(np.random.uniform(10, 100, self.N),0),
            'Hauteur': np.round(np.random.uniform(10, 100, self.N),0),
            'Poids_max': np.round(np.random.uniform(2, 10, self.N),0),
            'Prix': np.round(np.random.uniform(10, 100, self.N),0),
            'Quantite': np.random.randint(20, 100, self.N),
            'Type' : np.random.choice(['Box','Crate', 'Container'],size=self.N)

        }
        
        # Filtrer les données p

        df = pd.DataFrame(data)
        df = df[df['Longueur'] > df['Largeur']]
        df.reset_index(drop=True, inplace=True)
        df.drop_duplicates(inplace=True)

        return df
    def get_volume(self):
        return self.df['Longueur'] * self.df['Largeur'] * self.df['Hauteur']
    
    def get_max_weights(self):
        return self.df['Poids_max'] 



def create_bins(df):
    
  df_copie = df.copy()

  df_copie["Longueur"] = df_copie["Longueur"] * df_copie["Quantite"]
  df_copie["Largeur"] = df_copie["Largeur"] * df_copie["Quantite"]
  df_copie["Hauteur"] = df_copie["Hauteur"] * df_copie["Quantite"]
  df_copie["Poids_max"] = df_copie["Poids"] * df_copie["Quantite"]

  df_copie["Quantite"] = np.random.randint(1, 11, df_copie.shape[0])
  df_copie["Prix"] = np.round(np.random.uniform(10, 100, df_copie.shape[0]),0)
  df_copie["Type"] = np.random.choice(['Box','Crate', 'Container'],size=df_copie.shape[0])

  return df_copie[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]