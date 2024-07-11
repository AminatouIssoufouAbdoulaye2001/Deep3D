import pandas as pd
import numpy as np

# Fixing the random seed for reproducibility
np.random.seed(42)

# Defining the ranges for the variables
L_values = np.arange(10, 31)  # 10 to 30 inclusive
l_values = np.arange(5, 21)   # 5 to 20 inclusive
h_values = np.arange(4, 26)   # 4 to 25 inclusive
Poids_values = np.arange(30, 81)  # 30 to 80 inclusive

# Creating a grid of all possible combinations
nb = 500
data = pd.DataFrame({
    'Longueur': np.random.choice(L_values, nb),
    'Largeur': np.random.choice(l_values, nb),
    'Hauteur': np.random.choice(h_values, nb),
    'Poids_max': np.random.choice(Poids_values, nb)
})

# Assigning random prices and quantities
data['Prix'] = np.round(np.random.uniform(50, 100, size=len(data)), 2)  # Random prices between 50 and 500
data['Quantite'] = np.random.randint(1, 10, size=len(data))  # Random quantities between 1 and 100

# Assigning random types
data['Type'] = np.random.choice(['conteneur', 'carton'], size=len(data))

# Displaying the first few rows of the DataFrame
data = data[["Type", "Longueur", "Largeur", "Hauteur", "Poids_max", "Prix","Quantite"]]
data = data.drop_duplicates(subset=[ "Longueur", "Largeur", "Hauteur", "Poids_max","Quantite"]).reset_index()
print(data)
data.to_csv("data/bins.csv", index = False)