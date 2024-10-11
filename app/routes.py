#bibliothéques pour les différentes fonctionnalité de l'app
from datetime import date as dt_date
import datetime
from datetime import timedelta
import sys
import os
from functools import wraps
import secrets
from PIL import Image
from flask import abort, g, jsonify, render_template, session, url_for, flash, redirect, request,Response
from flask_paginate import Pagination

from sqlalchemy import  func
from app import app, db, bcrypt, mail
from app.forms import (ConteneurForm, RegistrationForm, LoginForm, UpdateAccountForm,
                       ArticleForm, RequestResetForm, ResetPasswordForm,
                       Updatepassword, UpdateAccountForm, Updatepassword,AjouterAdress)
from app.models import Commande, Conteneur, User, Article, Adresse
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import csv
#bibliothéques pour les graphiques
from io import StringIO
from plotly.offline import plot
import pandas as pd
import plotly.graph_objs as go
from playsound import playsound
from app.models import *
sys.path.append(os.path.join(os.path.dirname(__file__), 'app/models_rl'))
from app.models_rl.bin import *

number_articles_per_page = 10
number_commandes_per_page = 10

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about")
def about():

    return render_template('user_dashboard/about.html')
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérification si l'utilisateur est connecté et est admin
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Vous n'avez pas la permission d'accéder à cette page.", "danger")
            return redirect(url_for('login'))  # Redirection vers la page de login si non admin
        return f(*args, **kwargs)
    return decorated_function

@app.route("/acceuil_admin")
@login_required
@admin_required
def acceuil_admin():
    some_threshold = 4
    nombres_commandes = Commande.query.count()
    nombre_conteneurs = Conteneur.query.count()
    conteneurs = Conteneur.query.all()
    nombre_clients = User.query.count()
    nombre_articles = Article.query.count()
    dates, conteneurs = fetch_data_conteneurs()

        # Récupérer les données pour les commandes du mois dernier
    total_emballe, total_attente = fetch_commandes_status_totals()
    # Récupérer les données
    nombre_commandes = fetch_commandes_par_client()
    
    colors = ['#49895E' if val <= some_threshold else '#ebab54' for val in nombre_commandes]

    fig = go.Figure(data=[go.Histogram(x=nombre_commandes, nbinsx=20, marker=dict(color=colors),
                                hovertemplate='Nombre de commandes: %{x}<br>Nombre de clients: %{y}<extra></extra>')])

    # Mise à jour du layout pour ajouter un titre et des labels
    fig.update_layout(
        title_text='Nombre de Commandes par Client',
        xaxis_title_text='Nombre de Commandes',
        yaxis_title_text='Nombre de Clients',
        bargap=0.2,  # Espace entre les barres
        bargroupgap=0.1  # Espace entre les groupes de barres (si plusieurs séries)
    )
    graph_htmlhistogram = plot(fig, output_type='div')


    # Labels et valeurs pour le diagramme en camembert
    labels = ['Emballer', 'En attente']
    values = [total_emballe, total_attente]

    # Couleurs pour chaque segment du pie chart
    colors = ['#49495E', '#ebab54']

    # Création du diagramme en camembert
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=.3)])

    # Mise à jour du layout pour ajouter un titre
    fig.update_layout(title_text='Répartition des Commandes Emballées et En Attente du Mois')

    # Générer le code HTML pour le graphique
    graph_htmlcommandes = plot(fig, output_type='div')

    # Création du graphique des conteneurs crées par jours
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=conteneurs, mode='lines+markers', name='Conteneur', line=dict(color='#ebab54')))

    # Mettre à jour la mise en page du graphique
    fig.update_layout(
        title='Évolution quotidienne des conteneurs créées',
        xaxis_title='Date',
        yaxis_title='Nombre de commandes',
        xaxis=dict(tickformat='%d-%m'),
        xaxis_tickangle=-45, 
    )
    # Générer le code HTML pour le graphique des commandes
    graph_htmlconteneurs = plot(fig, output_type='div')
    # Interrogation de la base de données pour compter les articles par type de SKU
    data = db.session.query(Conteneur.type_conteneur, db.func.count(Conteneur.id)).group_by(Conteneur.type_conteneur).all()
    data = pd.DataFrame(data, columns=['type_conteneur', 'count'])

    # Création du graphique en barres par type de Sku
    fig = go.Figure(data=[go.Bar(
        x=data['type_conteneur'],
        y=data['count'],
        marker_color=['#49495E', '#ebab54', '#49495E', '#ebab54']  # Différentes couleurs pour chaque type de SKU
    )])

    fig.update_layout(
        title='Nombre de conteneur par type',
        xaxis_title='Type de conteneur',
        yaxis_title='Nombre de conteneur',
        xaxis=dict(type='category'),  # Catégorise l'axe des x
        bargap=0.7,  # Espacement entre les barres
        bargroupgap=0.1,  # Espacement entre les groupes de barres
        xaxis_tickangle=-45, 
    )
    graph_htmlbartype = plot(fig, output_type='div')
    return render_template('admin_dashboard/acceuil.html',nombre_articles=nombre_articles, nombre_clients= nombre_clients, nombres_commandes=nombres_commandes, conteneurs=conteneurs, graph_htmlcommandes=graph_htmlcommandes, graph_htmlhistogram=graph_htmlhistogram,  graph_htmlbartype=graph_htmlbartype, nombre_conteneurs=nombre_conteneurs, graph_htmlconteneurs=graph_htmlconteneurs)

@app.route("/acceuil_client")
@login_required
def acceuil_client():
       # Filtrer les commandes restantes ayant au moins un article
    nombre_articles = Article.query.filter_by(user_id=current_user.id).count()
    nombre_commandes = Commande.query.filter_by(user_id=current_user.id).count()
    # Récupérer les articles de la base de données
    commandes = current_user.commande
    articles = current_user.articles
    #Pagination
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)

    dates, articles, commandes = fetch_data(user_id=current_user.id)

    # Création du graphique des articles crées par jours
    dates, articles = fetch_data_articles(user_id=current_user.id)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=articles, mode='lines+markers', name='Articles', line=dict(color='#49495E',shape='spline')))
    fig.update_layout(
        title='Évolution des articles créés par Mois',
        xaxis_title='Date',
        yaxis_title='Nombre',
        xaxis=dict(tickformat='%d-%m')
    )

    graph_htmlarticle = plot(fig, output_type='div')

    dates, commandes = fetch_data_commandes(user_id=current_user.id)

    # Création du graphique des commandes crées par jours
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=commandes, mode='lines+markers', name='Commandes', line=dict(color='#ebab54')))

    # Mettre à jour la mise en page du graphique
    fig.update_layout(
        title='Évolution des commandes créées par Mois',
        xaxis_title='Date',
        yaxis_title='Nombre de commandes',
        xaxis=dict(tickformat='%d-%m')
    )
    # Générer le code HTML pour le graphique des commandes
    graph_htmlcommandes = plot(fig, output_type='div')

     # Création du graphique en pie pour les articles et commandes
    total_articles, total_commandes = fetch_totals(user_id=current_user.id)

    labels = ['Articles', 'Commandes']
    values = [total_articles, total_commandes]
    colors = ['49495E', 'ebab54']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=.3)])
    fig.update_layout(title_text='Pourcentage des Articles et Commandes du Mois')

    graph_htmlpie = plot(fig, output_type='div')

    # Interrogation de la base de données pour compter les articles par type de SKU
    data = db.session.query(Article.fragile, db.func.count(Article.id)).group_by(Article.fragile).filter_by(user_id=current_user.id).all()
    data = pd.DataFrame(data, columns=['fragile', 'count'])

    # Création du graphique en barres par type de Sku
    fig = go.Figure(data=[go.Bar(
        x=data['fragile'],
        y=data['count'],
        marker_color=['#49495E', '#ebab54', '#49495E', '#ebab54']  # Différentes couleurs pour chaque type de SKU
    )])

    fig.update_layout(
        title='Nombre d\'articles Fragile',
        xaxis_title='Catégorie',
        yaxis_title='Nombre d\'articles',
        xaxis=dict(type='category'),  # Catégorise l'axe des x
        bargap=0.5,  # Espace entre les barres
        bargroupgap=0.1 
    )
    graph_htmlbar = plot(fig, output_type='div')
    # Récupérer les données pour les commandes du mois dernier
    total_emballe, total_attente = fetch_commandes_status_totals_per_user(user_id=current_user.id)

    # Labels et valeurs pour le diagramme en camembert
    labels = ['Emballé', 'En attente']
    values = [total_emballe, total_attente]

    # Couleurs pour chaque segment du pie chart
    colors = ['#49495E', '#ebab54']

    # Création du diagramme en camembert
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=.3)])

    # Mise à jour du layout pour ajouter un titre
    fig.update_layout(title_text='Répartition des Commandes Emballées et En Attente du Mois')

    # Générer le code HTML pour le graphique
    graph_htmlcommandesstatus = plot(fig, output_type='div')

    return render_template('user_dashboard/acceuil.html',graph_htmlcommandesstatus=graph_htmlcommandesstatus, graph_htmlbar=graph_htmlbar, graph_htmlpie=graph_htmlpie, graph_htmlarticle=graph_htmlarticle, graph_htmlcommandes=graph_htmlcommandes, nombre_articles=nombre_articles, articles_pagination=articles_pagination, nombre_commandes=nombre_commandes, articles=articles, commandes=commandes)


#Register
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('acceuil_client'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.mot_de_passe.data).decode('utf-8')
        user = User(nom=form.nom.data, prenom=form.prenom.data, email=form.email.data, mot_de_passe=hashed_password, is_admin=False, adresse=None, image='default.jpg', telephone=None, code_enregistrement=None)
        db.session.add(user)
        db.session.commit()
        flash("Enregistrement réussi ! Veuillez vous connecter.", 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
#Fin Register

# Connexion
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('acceuil_client'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.mot_de_passe, form.mot_de_passe.data):
            if user.active:  # Vérification de l'état actif du compte utilisateur
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                if current_user.is_admin:
                    return redirect(next_page) if next_page else redirect(url_for('acceuil_admin'))
                else:
                    return redirect(next_page) if next_page else redirect(url_for('acceuil_client'))
            else:
                flash('Votre compte a été désactivé par l\'administrateur. Veuillez contacter le support.', 'danger')
        else:  
            flash('Connexion échouée. Veuillez vérifier votre email et votre mot de passe', 'danger')
            
    return render_template('login.html', title='Login', form=form)


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.is_admin:
        # Vérifie si l'utilisateur est un administrateur
        return render_template('admin_dashboard.html')
    else:
        abort(403)  # Accès interdit pour les utilisateurs non-administrateurs
#Fin connexion
@app.route('/user/<int:user_id>/toggle_active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active  # Inverse l'état d'activation
    db.session.commit()
    if user.active:
        message='L\'utilisateur a été activé avec succès.'
    else:
        message='L\'utilisateur a été désactivé avec succès.'

    flash(message, 'success')
    return redirect(url_for('list_clients'))  # Redirige vers la page d'administration

#Modification du mot de passe par Email
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Réinitialisation de votre mot de passe Deep3D',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Vous avez demandé une réinitialisation de votre mot de passe : suivez le lien ci-dessous pour le modifier.
Lien (URL) :
{url_for('reset_token', token=token, _external=True)}

Vous serez redirigé(e) vers une page sécurisée pour définir votre nouveau mot de passe. 
Ce lien est valable une fois et pour une durée de 30 minutes. Passé ce délai, vous devrez effectuer une nouvelle demande.
Si vous n'êtes pas à l'origine de cette demande, ne tenez pas compte de cet e-mail.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Un e-mail a été envoyé avec des instructions pour réinitialiser votre mot de passe.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Seesion Invalide ou token expiré', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.mot_de_passe.data).decode('utf-8')
        user.mot_de_passe = hashed_password
        db.session.commit()
        flash('Votre mot de passe a été mis à jour! Vous pouvez maintenant vous connecter', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
#Fin Modification


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
#Téléchargement d'image
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    form_picture.save(picture_path)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

#Affichage de l'image global
@app.before_request
def before_request():
    if current_user.is_authenticated:
        # Définition de l'image dans le contexte global g
        g.image = url_for('static', filename='images/' + current_user.image) if current_user.image else None
    else:
        g.image = None

#Création de fichier csv pour les articles sélectionnés
@app.route("/download_articles", methods=['POST'])
@login_required
def download_articles():
    selected_article_ids = request.form.getlist('selected_articles')

    articles = []
    if selected_article_ids:
        # Télécharger les articles sélectionnés
        articles = Article.query.filter(Article.id.in_(selected_article_ids)).all()
    else:
        # Télécharger tous les articles
        articles = Article.query.all()

    # Créer un fichier CSV ou TXT avec les données des articles
    output = StringIO()
    fieldnames = ['sku', 'largeur', 'longueur', 'hauteur', 'poids', 'quantite', 'fragile']
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    if articles:
        writer.writeheader()
        for article in articles:
            writer.writerow({
                'sku': article.sku,
                'largeur': article.largeur,
                'longueur': article.longueur,
                'hauteur': article.hauteur,
                'poids': article.poids,
                'quantite': article.quantite,
                'fragile': article.fragile
            })

        # Définir le type de contenu en fonction de l'extension du fichier
        content_type = 'text/csv' if request.form.get('file_format') == 'csv' else 'text/plain'

        # Retourner le contenu du fichier en tant que réponse HTTP
        response = Response(output.getvalue(), content_type=content_type)
        file_format = request.form.get('file_format', 'csv') 
        response.headers["Content-Disposition"] = "attachment; filename=articles_data." + file_format

        return response
    else:
        flash('Aucun article trouvé pour téléchargement.', 'warning')
        return redirect(url_for('acceuil_client'))


@app.route("/download_conteneur", methods=['POST'])
@login_required
@admin_required
def download_conteneur():
    selected_conteneur_ids = request.form.getlist('selected_conteneurs')

    if selected_conteneur_ids:
        # Télécharger les conteneurs sélectionnés
        conteneurs = Conteneur.query.filter(Conteneur.id.in_(selected_conteneur_ids)).all()
    else:
        # Télécharger tous les conteneurs
        conteneurs = Conteneur.query.all()

    if not conteneurs:
        flash('Aucun conteneur trouvé pour téléchargement.', 'warning')
        return redirect(url_for('acceuil_admin'))

    # Créer un fichier CSV avec les données des conteneurs
    output = StringIO()
    fieldnames = ['type_conteneur', 'largeur', 'longueur', 'hauteur', 'Poid_maximal', 'quantite', 'prix']
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for conteneur in conteneurs:
        writer.writerow({
            'type_conteneur': conteneur.type_conteneur,
            'largeur': conteneur.largeur,
            'longueur': conteneur.longueur,
            'hauteur': conteneur.hauteur,
            'Poid_maximal': conteneur.Poid_maximal,
            'quantite': conteneur.quantite,
            'prix': conteneur.prix
        })

    content_type = 'text/csv'
    response = Response(output.getvalue(), content_type=content_type)
    response.headers["Content-Disposition"] = f"attachment; filename=conteneurs_data.csv"

    return response



#Création d'article
@app.route("/new_article", methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    page = request.args.get('page', 1, type=int)
    #articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)


    '''for article in articles_pagination:
        article.largeur = int(article.largeur)
        article.longueur = int(article.longueur)
        article.hauteur = int(article.hauteur)
        article.poids = int(article.poids)'''
        
    #articles = Article.query.all() 
    if form.is_submitted() and form.validate():
        article = Article(sku=form.sku.data, largeur=form.largeur.data,
                          longueur=form.longueur.data, hauteur=form.hauteur.data,
                          poids=form.poids.data, quantite=form.quantite.data,
                          fragile=form.fragile.data,date_creation=dt_date.today(), user_id=current_user.id)
        
        db.session.add(article)
        db.session.commit()
        flash('Article bien enregistré!', 'success')
        return redirect(url_for('new_article'))
    


    nombre_articles = Article.query.filter_by(user_id=current_user.id).count()
    search_article = request.args.get('search_article')
    per_page = 5 
            # Nombre d'éléments affichés
  

    if search_article:
        articles_query = Article.query.filter((Article.sku.ilike(f'%{search_article}%')))
    else:
        articles_query = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc())

    articles_pagination = articles_query.paginate(page=page, per_page=number_articles_per_page, error_out=False)
    pagination_args = Pagination(page=page, per_page=per_page, total=nombre_articles, css_framework='bootstrap4')
    articles = articles_pagination.items

    # Si aucun article n'est trouvé, afficher un message
    #if not articles:
        #flash("Aucun article trouvé pour votre recherche.", "warning")

    per_page = articles_pagination.per_page
    page = articles_pagination.page
    start_index = (page - 1) * per_page + 1
    end_index = min(page * per_page, nombre_articles)
    #total_stock = sum(article.quantite for article in articles)  # Calcul du stock total
    '''total_stock = Article.query.filter_by(user_id=current_user.id).count()

   if total_stock < 10 and not session.get('alert_displayed') and current_user.id ==current_user.id:
        flash('Attention ! Le stock total des articles est inférieur à 10.', 'warning')
        session['alert_displayed'] = True
        # Vérifier si le son d'alerte a déjà été joué pour cet utilisateur
        if not session.get('alert_sound_played') and current_user.id==current_user.id:
            for i in range(0, 2):
                playsound("app/static/audio/bip.mp3")  # Jouer le fichier audio
            # Marquer que le son d'alerte a été joué pour cet utilisateur
            session['alert_sound_played'] = True'''

    return render_template('user_dashboard/create_article.html', title='New Article',pagination_args=pagination_args, start_index=start_index, end_index=end_index,  form=form, articles=articles, articles_pagination=articles_pagination)

@app.route("/article/<int:article_id>")
def get_article(id):
    article = Article.query.get_or_404(id)
    return render_template('user_dashboard/create_article.html', article=article)

#Création de commande
@app.route('/create_commande', methods=['POST'])
@login_required
def create_commande():
    selected_articles = request.form.getlist('selected_articles')
    if not selected_articles:
        flash('Aucun article sélectionné', 'danger')
        return redirect(url_for('article'))

    # Créer et sauvegarder la commande
    commande = Commande(date_creation=dt_date.today(), user_id=current_user.id)
    for article_id in selected_articles:
        article = Article.query.get(article_id)
        if article:
            commande.articles.append(article)
    db.session.add(commande)
    db.session.commit()

    # Clear the session after successful creation
    session.pop('selected_articles', None)
    flash('Commande créée avec succès !', 'success')
    user_commandes = Commande.query.filter_by(user_id=current_user.id)
    return redirect(url_for('article',commandes=user_commandes))



@app.route('/details_commande/<int:commande_id>')
def details_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    return render_template('user_dashboard/details_commande.html', title='Détails de la Commande', commande=commande)


#Création du conteneur

@app.route("/admin/new_conteneur", methods=['GET', 'POST'])
@admin_required
@login_required
def new_conteneur():
    form = ConteneurForm()
    if form.validate_on_submit():
        # Création du conteneur
        conteneur = Conteneur(type_conteneur=form.type_conteneur.data, largeur=form.largeur.data,
                          longueur=form.longueur.data, hauteur=form.hauteur.data,
                          Poid_maximal=form.Poid_maximal.data, quantite=form.quantite.data,
                          prix=form.prix.data, date_creation=dt_date.today())
        
        # Ajout à la base de données
        db.session.add(conteneur)
        db.session.commit()
        
        # Définir le chemin du fichier CSV
        csv_file = os.path.join('app/models_rl/data', 'bins.csv')
        
        # Lire le dernier index du fichier CSV
        last_index = 0
        if os.path.exists(csv_file):
            with open(csv_file, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    last_index = int(row['Index'])  # Met à jour avec le dernier index
        
        # Incrémenter l'index pour le nouveau conteneur
        new_index = last_index + 1
        

        # Ajouter les données du conteneur dans le fichier CSV avec l'index incrémenté
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Écrire l'en-tête si le fichier est vide
            if last_index == 0:
                writer.writerow(['Index', 'Type', 'Longueur', 'Largeur', 'Hauteur', 'Poids_max', 'Prix', 'Quantite'])
            writer.writerow([new_index, conteneur.type_conteneur, conteneur.longueur, conteneur.largeur, 
                             conteneur.hauteur, conteneur.Poid_maximal, conteneur.prix, conteneur.quantite])
        
        flash('Conteneur ajouté avec succès!', 'success')
        return redirect(url_for('new_conteneur'))

    # Gestion de la pagination et recherche (non modifiée)
    total_conteneurs = Conteneur.query.count()
    search_conteneur = request.args.get('search_conteneur')
    conteneurs_page = request.args.get('conteneurs_page', 1, type=int)
    per_page = 5 
            # Nombre d'éléments affichés
  

    if search_conteneur:
        conteneurs_query = Conteneur.query.filter((Conteneur.type_conteneur.ilike(f'%{search_conteneur}%')))
    else:
        conteneurs_query = Conteneur.query.order_by(Conteneur.id.desc())

    conteneurs_pagination = conteneurs_query.paginate(page=conteneurs_page, per_page=per_page, error_out=False)
    pagination_args = Pagination(page=conteneurs_page, per_page=per_page, total=conteneurs_query.count(), css_framework='bootstrap4')
    start_index = (conteneurs_pagination.page - 1) * conteneurs_pagination.per_page + 1
    end_index = min(conteneurs_pagination.page * conteneurs_pagination.per_page, conteneurs_query.count())
    conteneurs = conteneurs_pagination.items

    
    return render_template('admin_dashboard/conteneur.html',start_index=start_index, end_index=end_index,total_conteneurs=total_conteneurs,  form=form, conteneurs=conteneurs, conteneurs_pagination=conteneurs_pagination, pagination_args=pagination_args)
#Fin création
#Création du conteneur
@app.route("/alert_stock_conteneur", methods=['GET', 'POST'])
@login_required
def alert_stock_conteneur():
    total_stock = Conteneur.query.count()

    if total_stock < 10:
        flash('Attention ! Le stock total des conteneurs est inférieur à 10.', 'warning')
        for i in range(0, 2):
            playsound("app/static/audio/bip.mp3")  # Jouer le fichier audio

    # Appeler la fonction d'alerte dans un thread séparé

    # Rediriger vers la vue de création de conteneur
    return redirect(url_for('new_conteneur'))


@app.route("/articles", methods=['GET', 'POST'])
@login_required
def article():
    selected_articles = session.get('selected_articles', [])  # Récupérer les articles sélectionnés depuis la session

    # Pagination des articles
    page = request.args.get('page', 1, type=int)
    number_articles_per_page = 40  # Nombre d'articles par page
    articles_query = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc())
    articles_pagination = articles_query.paginate(page=page, per_page=number_articles_per_page, error_out=False)
    
    # Calculer les indices pour les articles
    start_index = (articles_pagination.page - 1) * articles_pagination.per_page + 1
    end_index = min(articles_pagination.page * articles_pagination.per_page, articles_query.count())
    user_commandes = Commande.query.filter_by(user_id=current_user.id).all()
    search_commandes = request.args.get('search_commandes')
    #page = request.args.get('page', 1, type=int)

    # Gestion de la pagination et recherche (non modifiée)
    #total_comandes = Commande.query.filter_by(user_id=current_user.id).count()
    search_commandes = request.args.get('search_commandes')
    commande_page = request.args.get('commande_page', 1, type=int)
    per_page = 5
            # Nombre d'éléments affichés
  

    if search_commandes:
        commandes_query = Commande.query.filter(
            Commande.user_id == current_user.id,  # Filtre par utilisateur
            (
                Commande.numero_commande.ilike(f'%{search_commandes}%') |
            (   Commande.date_creation.ilike(f'%{search_commandes}%')) |
                Commande.status.ilike(f'%{search_commandes}%')
            )
        )
    else:
        commandes_query = Commande.query.filter_by(user_id=current_user.id).order_by(Commande.id.desc())

    commandes_pagination = commandes_query.paginate(page=commande_page, per_page=per_page, error_out=False)
    pagination_args = Pagination(page=commande_page, per_page=per_page, total=commandes_query.count(), css_framework='bootstrap4')
    # Calcul des indices pour les commandes
    start_indexc = (commandes_pagination.page - 1) * commandes_pagination.per_page + 1
    end_indexc = min(commandes_pagination.page * commandes_pagination.per_page, commandes_query.count())
    commandes = commandes_pagination.items
    print(f"Nombre de commandes trouvées: {commandes_query.count()}")

    # Filtrer et supprimer les commandes qui ont 0 article
    for commande in user_commandes:
        if len(commande.articles) == 0:
            db.session.delete(commande)
    user_commandes = [commande for commande in Commande.query.filter_by(user_id=current_user.id).all() if len(commande.articles) > 0]


    # Mettre à jour la liste des commandes de l'utilisateur après la suppression

    return render_template(
        'user_dashboard/list_article.html',
        selected_articles=selected_articles,
        start_index=start_index,
        end_index=end_index,
        start_indexc=start_indexc,
        end_indexc=end_indexc,
        articles=articles_pagination.items,
        articles_pagination=articles_pagination,
        commandes_pagination=commandes_pagination,
        commandes=commandes,
        pagination_args=pagination_args,
        user_commandes=user_commandes
    )


@app.route("/admin/list_clients")
@login_required
@admin_required
def list_clients():
    search = request.args.get('search')
    users_page = request.args.get('users_page', 1, type=int)
    per_page = 10  # Nombre d'items par page

    if search:
        users_query = User.query.filter(
            ((User.prenom.ilike(f'%{search}%')) | (User.nom.ilike(f'%{search}%'))) &
            (User.is_admin != True)
        )
    else:
        users_query = User.query.filter(User.is_admin!=True).order_by(User.id.asc())

    users_pagination = users_query.paginate(page=users_page, per_page=per_page, error_out=False)
    pagination_args = Pagination(page=users_page, per_page=per_page, total=users_query.count(), css_framework='bootstrap4')
    total_clients = users_pagination.items

    return render_template('admin_dashboard/list_clients.html', users_pagination=users_pagination,pagination_args=pagination_args, total_clients=total_clients)
@app.route("/admin/list_commandes")
@login_required
@admin_required
def list_commandes():
    search_commande = request.args.get('search_commande')
    commandes_page = request.args.get('commandes_page', 1, type=int)
    per_page = 10 # Nombre d'items par page
    articles = current_user.articles
    #nombre_commandes=Commande.query.count

    commandes_query = Commande.query.all()

    if search_commande:
        commandes_query = Commande.query.filter((Commande.numero_commande.ilike(f'%{search_commande}%')) | (Commande.date_creation.ilike(f'%{search_commande}%')) |(Commande.status.ilike(f'%{search_commande}%')))
    else:
        commandes_query = Commande.query.order_by(Commande.id.desc())
    commandes_pagination = commandes_query.paginate(page=commandes_page, per_page=per_page, error_out=False)
    pagination_args = Pagination(page=commandes_page, per_page=per_page, total=commandes_query.count(), css_framework='bootstrap4')
    nombre_commandes = commandes_pagination.items

    return render_template('admin_dashboard/list_commandes.html', nombre_commandes=nombre_commandes, articles=articles,commandes_pagination=commandes_pagination,pagination_args=pagination_args,commandes=commandes_query)
@app.route('/update_commande_status', methods=['POST'])
@login_required
def update_commande_status():
    data = request.get_json()
    commande_id = data.get('id')
    new_status = data.get('status')

    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401

    commande = Commande.query.get(commande_id)
    if commande:
        commande.status = new_status
        db.session.commit()
        flash('Votre commande a bien été  emballée.', 'success')
        return jsonify({'success': True})
    else:
        flash('Commande non trouvée', 'error')
        return jsonify({'success': False, 'error': 'Commande non trouvée'}), 404

@app.route('/get_articles/<int:commande_id>')
def get_articles(commande_id):
    # Récupérer les articles associés à la commande spécifique avec l'ID commande_id
    commande = Commande.query.get_or_404(commande_id)

    articles_data = []
    for article in commande.articles:
        article_dict = {
            'sku': article.sku,
            'largeur': article.largeur,
            'longueur': article.longueur,
            'hauteur': article.hauteur,
            'poids': article.poids,
            'quantite': article.quantite,
            'fragile': article.fragile,
            'commande_id': commande_id  
        }
        articles_data.append(article_dict)

    return jsonify(articles_data)

@app.route('/pack_articles', methods=['POST'])
def pack_articles():
    data = request.json  # Get JSON data from request
    commande_id = data['commande_id']  # Get commandeId from the data

    # Retrieve articles associated with commandeId from the database
    commande = Commande.query.get_or_404(commande_id)
    articles = []
    for article in commande.articles:
        article_dict = {
            'sku': article.sku,
            'largeur': article.largeur,
            'longueur': article.longueur,
            'hauteur': article.hauteur,
            'poids': article.poids,
            'quantite': article.quantite,
            'fragile': article.fragile,
            'commande_id': commande_id  
        }
        articles.append(article_dict)

    # Process and pack the articles using your Python logic
    pack_articles, non_pack_articles = model_pack_articles(articles)

    pack_articles["nb_bin"] = len(list(pack_articles["ID Carton"].unique()))
    
    result = pack_articles.to_dict(orient='records')
    dict_non_pack = {}
    if len(non_pack_articles)==0:
        dict_non_pack["non_pack_articles"] = 0
        result.append(dict_non_pack)
    else :
        dict_non_pack = {}
        dict_non_pack["non_pack_articles"] = int(non_pack_articles.Quantite_key.sum())
        dict_non_pack['sku'] = list(non_pack_articles.sku)
        dict_non_pack['Quantite_key'] = list(non_pack_articles.Quantite_key)
        result.append(dict_non_pack)



    # Return a response indicating success or failure
    return jsonify(result)
#Fin Affichage

#les Différentes modification apporté au seins des différentes fonctionnalités

#Modification du Mot de passe Clients
@app.route("/update_password", methods=['GET', 'POST'])
@login_required
def securite():
    form_password = Updatepassword()  # Formulaire de mise à jour du mot de passe

    if current_user.is_admin:
        
        return admin_securite()
    
    if form_password.validate_on_submit():
        # Mettre à jour le mot de passe de l'utilisateur
        if form_password.mot_de_passe.data != current_user.mot_de_passe:
            hashed_password = bcrypt.generate_password_hash(form_password.mot_de_passe.data).decode('utf-8')
            current_user.mot_de_passe = hashed_password
            db.session.commit()
            flash('Votre mot de passe a été mis à jour avec succès.', 'success')
            return redirect(url_for('securite'))
        else:
            flash('Le nouveau mot de passe doit être différent de l\'ancien.', 'danger')
            return redirect(url_for('securite')) 
    
    return render_template('user_dashboard/update_password.html', form_password=form_password)

#Modification du Mot de passe Admin
@app.route("/admin/update_password", methods=['GET', 'POST'])
@login_required
def admin_securite():

    form_password = Updatepassword()  # Formulaire de mise à jour du mot de passe

    if form_password.validate_on_submit():
        # Mettre à jour le mot de passe de l'utilisateur
        if form_password.mot_de_passe.data != current_user.mot_de_passe:
            hashed_password = bcrypt.generate_password_hash(form_password.mot_de_passe.data).decode('utf-8')
            current_user.mot_de_passe = hashed_password
            db.session.commit()
            flash('Votre mot de passe a été mis à jour avec succès.', 'success')
            return redirect(url_for('admin_securite'))
        else:
            flash('Le nouveau mot de passe doit être différent de l\'ancien.', 'danger')
            return redirect(url_for('admin_securite')) 

    return render_template('admin_dashboard/update_password.html', form_password=form_password)

#Mises à jour du compte Clients
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    existing_address = Adresse.query.filter_by(user_id=current_user.id).first()
    form_account = UpdateAccountForm()
    form_newadresse = AjouterAdress()

    if current_user.is_admin:
        
        return account_admin()

    if form_account.validate_on_submit():
        if form_account.email.data != current_user.email and User.query.filter_by(email=form_account.email.data).first():
            flash('Cet email est déjà utilisé par un autre utilisateur. Veuillez en choisir un autre.', 'danger')
        else:
            if form_account.image.data:
                image = save_picture(form_account.image.data)
                current_user.image = image
            current_user.nom = form_account.nom.data
            current_user.prenom = form_account.prenom.data
            current_user.email = form_account.email.data
            current_user.telephone = form_account.telephone.data 
            db.session.commit()
            flash('Votre profil a été mis à jour!', 'success')

        return redirect(url_for('account'))
    if form_newadresse.validate_on_submit():
        if existing_address:
            # Modifier l'adresse existante
            existing_address.rue = form_newadresse.rue.data
            existing_address.code_postal = form_newadresse.code_postal.data
            existing_address.pays = form_newadresse.pays.data
            existing_address.ville = form_newadresse.ville.data
            message = 'Votre adresse a été modifiée avec succès!'
        else:
            # Ajouter une nouvelle adresse
            new_address = Adresse(
                rue=form_newadresse.rue.data,
                code_postal=form_newadresse.code_postal.data,
                pays=form_newadresse.pays.data,
                ville=form_newadresse.ville.data,
                user_id=current_user.id
            )
            db.session.add(new_address)
            message = 'Votre adresse a été ajoutée avec succès!'

        db.session.commit()
        flash(message, 'success')
        return redirect(url_for('account'))

    # Afficher les formulaires
    image = url_for('static', filename='images/' + current_user.image)
    form_account.nom.data = current_user.nom
    form_account.prenom.data = current_user.prenom
    form_account.email.data = current_user.email 
    form_account.telephone.data = current_user.telephone

    if existing_address:
        form_newadresse.rue.data = existing_address.rue
        form_newadresse.code_postal.data = existing_address.code_postal
        form_newadresse.pays.data = existing_address.pays
        form_newadresse.ville.data = existing_address.ville
    else:
        # Définir les valeurs par défaut pour un nouvel utilisateur
        form_newadresse.rue.data = ""
        form_newadresse.code_postal.data = ""
        form_newadresse.pays.data = ""
        form_newadresse.ville.data = ""

    return render_template('user_dashboard/account.html', image=image, title='Account', form_account=form_account, form_newadresse=form_newadresse,
                           existing_address=existing_address)

#Mises à jour du compte Admin
@app.route("/admin/account", methods=['GET', 'POST'])
@login_required
@admin_required
def account_admin():
    existing_address = Adresse.query.filter_by(user_id=current_user.id).first()
    form_account = UpdateAccountForm()
    form_newadresse = AjouterAdress()

    if form_account.validate_on_submit():
        if form_account.email.data != current_user.email and User.query.filter_by(email=form_account.email.data).first():
            flash('Cet email est déjà utilisé par un autre utilisateur. Veuillez en choisir un autre.', 'danger')
        else:
            if form_account.image.data:
                image = save_picture(form_account.image.data)
                current_user.image = image
            current_user.nom = form_account.nom.data
            current_user.prenom = form_account.prenom.data
            current_user.email = form_account.email.data
            current_user.telephone = form_account.telephone.data 
            db.session.commit()
            flash('Votre profil a été mis à jour!', 'success')

        return redirect(url_for('account'))
    if form_newadresse.validate_on_submit():
        if existing_address:
            # Modifier l'adresse existante
            existing_address.rue = form_newadresse.rue.data
            existing_address.code_postal = form_newadresse.code_postal.data
            existing_address.pays = form_newadresse.pays.data
            existing_address.ville = form_newadresse.ville.data
            message = 'Votre adresse a été modifiée avec succès!'
        else:
            # Ajouter une nouvelle adresse
            new_address = Adresse(
                rue=form_newadresse.rue.data,
                code_postal=form_newadresse.code_postal.data,
                pays=form_newadresse.pays.data,
                ville=form_newadresse.ville.data,
                user_id=current_user.id
            )
            db.session.add(new_address)
            message = 'Votre adresse a été ajoutée avec succès!'

        db.session.commit()
        flash(message, 'success')
        return redirect(url_for('account_admin'))

    # Afficher les formulaires
    form_account.nom.data = current_user.nom
    form_account.prenom.data = current_user.prenom
    form_account.email.data = current_user.email 
    form_account.telephone.data = current_user.telephone

    if existing_address:
        form_newadresse.rue.data = existing_address.rue
        form_newadresse.code_postal.data = existing_address.code_postal
        form_newadresse.pays.data = existing_address.pays
        form_newadresse.ville.data = existing_address.ville
    else:
        # Définir les valeurs par défaut pour un nouvel utilisateur
        form_newadresse.rue.data = ""
        form_newadresse.code_postal.data = ""
        form_newadresse.pays.data = ""
        form_newadresse.ville.data = ""
    return render_template('admin_dashboard/account.html', title='Account', form_account=form_account, form_newadresse=form_newadresse,
                           existing_address=existing_address)

#Mises à jour des articles
@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
@login_required
def update_article(id):
    article = Article.query.get_or_404(id)
    form = ArticleForm()
    if request.method == 'GET':
        form.sku.data = article.sku
        form.longueur.data = article.longueur
        form.largeur.data = article.largeur
        form.hauteur.data = article.hauteur
        form.poids.data = article.poids
        form.quantite.data = article.quantite
        form.fragile.data = article.fragile

    elif request.method == 'POST':
        article.sku = form.sku.data 
        article.longueur = form.longueur.data 
        article.largeur = form.largeur.data 
        article.hauteur = form.hauteur.data 
        article.poids = form.poids.data 
        article.quantite = form.quantite.data 
        article.fragile = form.fragile.data 

        db.session.commit()
        flash('Votre Article a été bien mise à jour!', 'success')
        return redirect(url_for('new_article'))
    
    return render_template('user_dashboard/create_article.html', title='Update article', form=form, article=article)


#Mises à jour des conteneurs
@app.route('/update_conteneur/<int:id>', methods=['GET', 'POST'])
@login_required
def update_conteneur(id):
    conteneur = Conteneur.query.get_or_404(id)
    form = ConteneurForm()
    if request.method == 'GET':
        form.type_conteneur.data = conteneur.type_conteneur
        form.longueur.data = conteneur.longueur
        form.largeur.data = conteneur.largeur
        form.hauteur.data = conteneur.hauteur
        form.Poid_maximal.data = conteneur.Poid_maximal
        form.quantite.data = conteneur.quantite
        form.prix.data = conteneur.prix

    elif request.method == 'POST':
        conteneur.type_conteneur = form.type_conteneur.data 
        conteneur.longueur = form.longueur.data 
        conteneur.largeur = form.largeur.data 
        conteneur.hauteur = form.hauteur.data 
        conteneur.Poid_maximal = form.Poid_maximal.data 
        conteneur.quantite = form.quantite.data 
        conteneur.prix = form.prix.data 

        db.session.commit()
        flash('Votre conteneur a été bien mise à jour!', 'success')
        return redirect(url_for('new_conteneur'))

    return render_template('admin_dashboard/conteneur.html', title='Update conteneur', form=form, conteneur=conteneur)
#Fim Modification


#Suppression des différentes fonctions

#Suppression des clients
@app.route("/user/<int:id>/delete", methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if not current_user.is_admin:
        abort(403)  # Si l'utilisateur n'est pas un administrateur, il ne peut pas supprimer d'utilisateurs
    db.session.delete(user)
    db.session.commit()
    flash('L\'utilisateur a été supprimé avec succès!', 'success')
    return redirect(url_for('list_clients'))

#Suppression des conteneurs
@app.route('/delete_conteneur/<int:id>', methods=['POST'])
@login_required
def delete_conteneur(id):
    conteneur = Conteneur.query.get_or_404(id)
    if not current_user.is_admin:
        abort(403)  # Si l'utilisateur n'est pas un administrateur, il ne peut pas supprimer de conteneur
    db.session.delete(conteneur)
    db.session.commit()
    flash('Le conteneur a été supprimé avec succès!', 'danger')
    return redirect(url_for('new_conteneur'))

#Suppression des articles
@app.route("/article/<int:id>/delete", methods=['POST'])
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)
    if article.user_id != current_user.id:
        abort(403)
    db.session.delete(article)
    db.session.commit()
    flash('Votre article a été supprimé!', 'success')
    return redirect(url_for('new_article'))

#Suppression des commandes
@app.route("/commande/<int:id>/delete", methods=['POST'])
@login_required
def delete_commande(id):
    commande = Commande.query.get_or_404(id)
    if commande.user_id != current_user.id:
        abort(403)
    db.session.delete(commande)
    db.session.commit()
    flash('Votre commande a été supprimé!', 'success')
    return redirect(url_for('article'))
        
#Fin Suppression














def fetch_data(user_id):
    today = dt_date.today()  # Obtenez la date actuelle en utilisant datetime.date
    week_ago = today - timedelta(days=7)

    article_counts = db.session.query(func.date(Article.date_creation), func.count(Article.id))\
        .filter(Article.date_creation >= week_ago, Article.user_id == user_id)\
        .group_by(func.date(Article.date_creation)).all()

    commande_counts = db.session.query(func.date(Commande.date_creation), func.count(Commande.id))\
        .filter(Commande.date_creation >= week_ago, Commande.user_id == user_id)\
        .group_by(func.date(Commande.date_creation)).all()

    dates = [week_ago + timedelta(days=i) for i in range(8)]
    articles = [0] * 8
    commandes = [0] * 8

    for date_str, count in article_counts:
        date = dt_date.fromisoformat(date_str)  # Utilisez la méthode fromisoformat de datetime.date
        index = (date - week_ago).days
        articles[index] = count

    for date_str, count in commande_counts:
        date = dt_date.fromisoformat(date_str)  # Utilisez la méthode fromisoformat de datetime.date
        index = (date - week_ago).days
        commandes[index] = count

    return dates, articles, commandes

def fetch_totals(user_id):
    week_ago = dt_date.today() - timedelta(days=30)
    total_articles = db.session.query(func.count(Article.id))\
        .filter(Article.date_creation >= week_ago, Article.user_id == user_id).scalar()
    total_commandes = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= week_ago, Commande.user_id == user_id).scalar()
    return total_articles, total_commandes

def fetch_data_articles(user_id):
    today = dt_date.today()  # Obtenez uniquement la date sans l'heure
    week_ago = today - timedelta(days=30)

    article_counts = db.session.query(func.date(Article.date_creation), func.count(Article.id))\
        .filter(Article.date_creation >= week_ago, Article.user_id == user_id)\
        .group_by(func.date(Article.date_creation)).all()

    dates = [week_ago + timedelta(days=i) for i in range(31)]
    articles = [0] * 31

    for date_str, count in article_counts:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()  # Convertissez la chaîne en objet date
        if isinstance(date_obj, datetime.date):
            index = (date_obj - week_ago).days  # Utilisez directement la soustraction pour obtenir le nombre de jours
            articles[index] = count

    return dates, articles


def fetch_data_commandes(user_id):
    today = dt_date.today()
    week_ago = today - timedelta(days=30)

    commande_counts = db.session.query(func.date(Commande.date_creation), func.count(Commande.id))\
        .filter(Commande.date_creation >= week_ago, Commande.user_id == user_id)\
        .group_by(func.date(Commande.date_creation)).all()

    dates = [week_ago + timedelta(days=i) for i in range(31)]
    commandes = [0] * 31

    for date_str, count in commande_counts:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()  # Convertissez la chaîne en objet date
        if isinstance(date_obj, datetime.date):
            index = (date_obj - week_ago).days
            commandes[index] = count

    return dates, commandes

def fetch_data_conteneurs():
    today = dt_date.today()
    month_ago = today - timedelta(days=30)

    conteneur_counts = db.session.query(func.date(Conteneur.date_creation), func.count(Conteneur.id))\
        .filter(Conteneur.date_creation >= month_ago)\
        .group_by(func.date(Conteneur.date_creation)).all()

    dates = [month_ago + timedelta(days=i) for i in range(31)]
    Conteneurs = [0] * 31

    for date_str, count in conteneur_counts:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()  # Convertissez la chaîne en objet date
        if isinstance(date_obj, datetime.date):
            index = (date_obj - month_ago).days
            Conteneurs[index] = count

    return dates, Conteneurs

def fetch_commandes_status_totals():
    month_ago = dt_date.today() - timedelta(days=30)  # Filtrer pour le dernier mois

    # Récupérer le nombre de commandes avec le status "emballé" pour le mois dernier
    total_emballe = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= month_ago, 
                Commande.status == 'Emballer').scalar()

    # Récupérer le nombre de commandes avec le status "en attente" pour le mois dernier
    total_attente = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= month_ago, 
                Commande.status == 'En Attente').scalar()

    return total_emballe, total_attente

def fetch_commandes_par_client():
    # Récupérer le nombre de commandes passées par chaque client
    commandes_par_client = db.session.query(Commande.user_id, func.count(Commande.id).label('nombre_commandes'))\
        .group_by(Commande.user_id).all()
    
    # Transformer en un format de liste pour l'histogramme
    nombre_commandes = [commande.nombre_commandes for commande in commandes_par_client]
    
    return nombre_commandes

def fetch_commandes_status_totals_per_user(user_id):
    month_ago = dt_date.today() - timedelta(days=30)  # Filtrer pour le dernier mois

    # Récupérer le nombre de commandes avec le statut "emballé" pour le mois dernier
    total_emballe = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= month_ago, 
                Commande.user_id == user_id, 
                Commande.status == 'Emballer').scalar()

    # Récupérer le nombre de commandes avec le statut "en attente" pour le mois dernier
    total_attente = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= month_ago, 
                Commande.user_id == user_id, 
                Commande.status == 'En Attente').scalar()

    return total_emballe, total_attente

@app.route("/charts")
@login_required
def charts():
    nb_articles =  current_user.articles  
    dates, articles, commandes = fetch_data(user_id=current_user.id)
        # Création du graphique combiné
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=articles, mode='lines+markers', name='Articles', line=dict(color='#49495E',shape='spline'),  fillcolor='rgba(0, 0, 0, 0.3)',  fill='tozeroy'))
    fig.add_trace(go.Scatter(x=dates, y=commandes, mode='lines+markers', name='Commandes', line=dict(color='#ebab54',shape='spline'),fillcolor='rgba(235, 160, 84, 0.3)', fill='tozeroy'))

    fig.update_layout(
        title='Évolution quotidienne des articles et des commandes créés',
        xaxis_title='Date',
        yaxis_title='Nombre',
        xaxis=dict(tickformat='%d-%m')
    )

    graphscatter_html = plot(fig, output_type='div')  
    return render_template('user_dashboard/statistique.html',nb_articles=nb_articles, graphscatter_html=graphscatter_html)
