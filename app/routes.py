             
#bibliothéques pour les différentes fonctionnalité de l'app
from datetime import datetime, timedelta
import os
import secrets
from PIL import Image
from flask import abort, render_template, url_for, flash, redirect, request,Response

from sqlalchemy import func
from app import app, db, bcrypt, mail
from app.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                       ArticleForm, RequestResetForm, ResetPasswordForm,
                       Updatepassword, UpdateAccountForm, Updatepassword,AjouterAdress)
from app.models import Commande, User, Article, Adresse
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import csv
#bibliothéques pour les graphiques
from io import StringIO
from scipy.interpolate import make_interp_spline
from matplotlib import pyplot as plt
from plotly.offline import plot
import numpy as np
import pandas as pd
import plotly.graph_objs as go


number_articles_per_page = 5
number_commandes_per_page = 5

@app.route("/")
def home():
    return render_template('home.html')



@app.route("/acceuil_admin")
def acceuil_admin():
    return render_template('admin_dashboard/acceuil.html')



@app.route("/acceuil_client")
@login_required
def acceuil_client():
       # Filtrer les commandes restantes ayant au moins un article

    nombre_articles = Article.query.filter_by(user_id=current_user.id).count()
    nombre_commandes = Commande.query.filter_by(user_id=current_user.id).count()
    # Récupérer les articles de la base de données
    article =  current_user.articles
    commandes = current_user.commande


    #Pagination
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)

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

    total_articles, total_commandes = fetch_totals(user_id=current_user.id)

    labels = ['Articles', 'Commandes']
    values = [total_articles, total_commandes]
    colors = ['49495E', 'ebab54']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=.3)])
    fig.update_layout(title_text='Pourcentage des Articles et Commandes de la dernière semaine')

    graph_htmlpie = plot(fig, output_type='div')

    # Interrogation de la base de données pour compter les articles par type de SKU
    data = db.session.query(Article.sku, db.func.count(Article.id)).group_by(Article.sku).filter_by(user_id=current_user.id).all()
    data = pd.DataFrame(data, columns=['sku', 'count'])

    # Création du graphique en barres
    fig = go.Figure(data=[go.Bar(
        x=data['sku'],
        y=data['count'],
        marker_color=['#49495E', '#ebab54', '#49495E', '#ebab54']  # Différentes couleurs pour chaque type de SKU
    )])

    fig.update_layout(
        title='Nombre d\'articles par type de SKU',
        xaxis_title='Type de SKU',
        yaxis_title='Nombre d\'articles',
        xaxis=dict(type='category')  # Catégorise l'axe des x
    )
    graph_htmlbar = plot(fig, output_type='div')

    return render_template('user_dashboard/acceuil.html', graph_htmlbar=graph_htmlbar, graph_htmlpie=graph_htmlpie, graphscatter_html=graphscatter_html, nombre_articles=nombre_articles, articles_pagination=articles_pagination, nombre_commandes=nombre_commandes, articles=article, commandes=commandes)


@app.route("/charts")
@login_required
def charts():
    nb_articles =  current_user.articles
    dates, articles = fetch_data_articles(user_id=current_user.id)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=articles, mode='lines+markers', name='Articles', line=dict(color='#49495E')))
    fig.update_layout(
        title='Évolution quotidienne des articles créés',
        xaxis_title='Date',
        yaxis_title='Nombre',
        xaxis=dict(tickformat='%d-%m')
    )

    graph_htmlarticle = plot(fig, output_type='div')

    dates, commandes = fetch_data_commandes(user_id=current_user.id)

    # Créer la trace pour les commandes
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=commandes, mode='lines+markers', name='Commandes', line=dict(color='#ebab54')))

    # Mettre à jour la mise en page du graphique
    fig.update_layout(
        title='Évolution quotidienne des commandes créées',
        xaxis_title='Date',
        yaxis_title='Nombre de commandes',
        xaxis=dict(tickformat='%d-%m')
    )

    # Générer le code HTML pour le graphique
    graph_htmlcommandes = plot(fig, output_type='div')
            
    return render_template('user_dashboard/statistique.html',graph_htmlarticle=graph_htmlarticle,graph_htmlcommandes=graph_htmlcommandes,nb_articles=nb_articles)

@app.route("/articles")
def article():

    articles = current_user.articles
    #Pagination des articles
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)
    
    #Pagination des commandes
    commande_page = request.args.get('commandes_page', 1, type=int)
    commandes_pagination = Commande.query.filter_by(user_id=current_user.id).order_by(Commande.id.desc()).paginate(page=commande_page, per_page=number_commandes_per_page, error_out=False)

    # Récupérer toutes les commandes de l'utilisateur
    user_commandes = Commande.query.filter_by(user_id=current_user.id).all()

    # Filtrer et supprimer les commandes qui ont 0 article
    for commande in user_commandes:
        if len(commande.articles) == 0:
            db.session.delete(commande)

    # Committer les suppressions
    db.session.commit()

    # Mettre à jour la liste des commandes de l'utilisateur après la suppression
    user_commandes = [commande for commande in user_commandes if len(commande.articles) > 0]
    # Rendre le template avec les données mises à jour
    return render_template('user_dashboard/list_article.html', articles=articles, articles_pagination=articles_pagination, commandes_pagination=commandes_pagination, commandes=user_commandes)


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


print("L'administrateur a été ajouté avec succès à la base de données.")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('acceuil_client'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.mot_de_passe, form.mot_de_passe.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if current_user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('acceuil_admin'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('acceuil_client'))   
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



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

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

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
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



@app.route("/update_password", methods=['GET', 'POST'])
@login_required
def securite():
    form_password = Updatepassword()  # Formulaire de mise à jour du mot de passe
    if form_password.validate_on_submit():
        # Mettre à jour le mot de passe de l'utilisateur
        if form_password.mot_de_passe.data != current_user.mot_de_passe:
            hashed_password = bcrypt.generate_password_hash(form_password.mot_de_passe.data).decode('utf-8')
            current_user.mot_de_passe = hashed_password
            db.session.commit()
            flash('Votre mot de passe a été mis à jour avec succès.', 'success')
            return redirect(url_for('account'))
        else:
            flash('Le nouveau mot de passe doit être différent de l\'ancien.', 'danger')
            return redirect(url_for('account')) 
    
    return render_template('user_dashboard/update_password.html', form_password=form_password)


@app.route("/new_article", methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)

    '''for article in articles_pagination:
        article.largeur = int(article.largeur)
        article.longueur = int(article.longueur)
        article.hauteur = int(article.hauteur)
        article.poids = int(article.poids)'''
        
    articles = articles_pagination.items
    #articles = Article.query.all() 
    if form.validate_on_submit():
        article = Article(sku=form.sku.data, largeur=form.largeur.data,
                          longueur=form.longueur.data, hauteur=form.hauteur.data,
                          poids=form.poids.data, quantite=form.quantite.data,
                          fragile=form.fragile.data,date_creation=datetime.now(), user_id=current_user.id)
        
        db.session.add(article)
        db.session.commit()
        flash('Article bien enregistré!', 'success')
        return redirect(url_for('new_article'))
    
    return render_template('user_dashboard/create_article.html', title='New Article', form=form, articles=articles, articles_pagination=articles_pagination)


@app.route("/article/<int:article_id>")
def get_article(id):
    article = Article.query.get_or_404(id)
    return render_template('user_dashboard/create_article.html', article=article)

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


@app.route('/create_commande', methods=['POST'])
@login_required
def create_commande():
    # Get selected article IDs from the form data
        selected_articles = request.form.getlist('selected_articles')  # This returns a list of selected article IDs
        if not selected_articles:
            flash('Aucun article selectionné', 'danger')
            return redirect(url_for('article'))

        # Create a new Commande object
        commande = Commande(date_creation=datetime.now(), user_id=current_user.id)  # Assuming Commande model has a date_creation field

        for article_id in selected_articles:
            article = Article.query.get(article_id)
            if article:
                commande.articles.append(article)
        # Save the commande object to the database
        db.session.add(commande)
        db.session.commit()

        # Flash a success message (optional)
        flash('Commande créée avec succès !', 'success')

        # Redirect to the current page after creating the commande (optional)
        user_commandes = Commande.query.filter_by(user_id=current_user.id)
        return redirect(url_for('article',commandes=user_commandes))

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
        



@app.route('/details_commande/<int:commande_id>')
def details_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    return render_template('user_dashboard/details_commande.html', title='Détails de la Commande', commande=commande)


def fetch_data(user_id):
    today = datetime.utcnow()
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

    for date, count in article_counts:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()  # Assurez-vous que le format de date correspond à ce que vous récupérez
        index = (date - week_ago.date()).days
        articles[index] = count

    for date, count in commande_counts:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()  # Même traitement pour les commandes
        index = (date - week_ago.date()).days
        commandes[index] = count

    return dates, articles, commandes

def fetch_totals(user_id):
    week_ago = datetime.utcnow() - timedelta(days=7)
    total_articles = db.session.query(func.count(Article.id))\
        .filter(Article.date_creation >= week_ago, Article.user_id == user_id).scalar()
    total_commandes = db.session.query(func.count(Commande.id))\
        .filter(Commande.date_creation >= week_ago, Commande.user_id == user_id).scalar()
    return total_articles, total_commandes

def fetch_data_articles(user_id):

    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)

    article_counts = db.session.query(func.date(Article.date_creation), func.count(Article.id))\
        .filter(Article.date_creation >= week_ago, Article.user_id == user_id)\
        .group_by(func.date(Article.date_creation)).all()


    dates = [week_ago + timedelta(days=i) for i in range(8)]
    articles = [0] * 8

    for date, count in article_counts:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()  # Assurez-vous que le format de date correspond à ce que vous récupérez
        index = (date - week_ago.date()).days
        articles[index] = count

    return dates, articles

def fetch_data_commandes(user_id):

    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)


    commande_counts = db.session.query(func.date(Commande.date_creation), func.count(Commande.id))\
        .filter(Commande.date_creation >= week_ago, Commande.user_id == user_id)\
        .group_by(func.date(Commande.date_creation)).all()

    dates = [week_ago + timedelta(days=i) for i in range(8)]
    commandes = [0] * 8
    for date, count in commande_counts:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()  # Même traitement pour les commandes
        index = (date - week_ago.date()).days
        commandes[index] = count

    return dates, commandes