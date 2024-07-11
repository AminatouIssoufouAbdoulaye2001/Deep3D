import pandas as pd

# Exemple de DataFrame initial
data = {
    "Longueur": [10, 20, 30],
    "Largeur": [5, 10, 15],
    "Hauteur": [2, 4, 6],
    "Quantite": [3, 2, 1],
    "Poids": [0.5, 1.0, 1.5]
}

df = pd.DataFrame(data)
print(df)

# Répliquer les lignes en fonction de la quantité
df_new = df.loc[df.index.repeat(df['Quantite'])].reset_index(drop=True)

# Mettre à jour la colonne Quantité pour qu'elle soit 1 pour chaque ligne
df_new['Quantite'] = 1

print(df_new)
