"""
from flask import Flask, request, jsonify
import pandas as pd
from io import StringIO
from app.models_rl.main_vf import *

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/process_form', methods=['POST'])
def process_form():
    data = request.json
    
    # Convert the data to CSV format
    df = pd.DataFrame([data])
    csv_data = StringIO()
    df.to_csv(csv_data, index=False)

    # Apply your function to the dataframe (example function)
    df_result = main_function() #example_function(df)
    
    # Convert the resulting dataframe to a list of dictionaries
    result = df_result.to_dict(orient='records')
    print("result : ", result)
    
    return jsonify(result)

def main_function():
        print("=============== Test modèle : ====================\n\n")
        df_article = pd.read_csv("data/articles_data.csv")
        new_names = {'longueur': 'Longueur', 'largeur': 'Largeur',
        "hauteur": "Hauteur", "poids": "Poids", "quantite": "Quantite"}
        df_article = df_article.rename(columns=new_names)
        df_article = df_article[['Longueur', 'Largeur', 'Hauteur', 'Poids', 'Quantite']]
        df_article = df_article[:4]
        print( "Nombre Articles : ", len(df_article)) 

        df_carton = pd.read_csv("data/conteneurs_data.csv")
        df_carton = df_carton[['Longueur', 'Largeur', 'Hauteur', 'Poids_max','Prix', 'Quantite', 'Type']]
        ## BIN PACK
        bin = Bin(df_article, df_carton)
        return bin.pack()




def example_function(df):
    # Example function that adds a new column
    df['new_column'] = df['name'] + ' - processed'
    return df

if __name__ == '__main__':
    app.run(debug=True)
"""