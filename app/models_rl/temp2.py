from flask import Flask, request

app = Flask(__name__)

@app.route('/pack', methods=['POST'])
def pack():
  if request.method == 'POST':
    # Exécuter le code Python ici
    
    # faire venir les données de la commande
    # df_article [longueur, largeur, hauteur, ...]

    ## faire venir les données sur les cartons disponibles
    # df_carton [long, larg, ...]
"""
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

        df.save("save/result1.txt")

    return "ok"
    """

if __name__ == '__main__':
  app.run(debug=True)


### Html
# lire le result1.txt

# afficher


