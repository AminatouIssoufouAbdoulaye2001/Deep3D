             
from collections import defaultdict
from datetime import datetime, timedelta
import os
import secrets
from PIL import Image
from flask import abort, jsonify, render_template, url_for, flash, redirect, request,Response
from app import app, db, bcrypt, mail
from app.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                       ArticleForm, RequestResetForm, ResetPasswordForm,
                       Updatepassword, UpdateAccountForm, Updatepassword,AjouterAdress)
from app.models import Commande, User, Article, Adresse
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import csv
from io import StringIO

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
    nombre_articles = Article.query.filter_by(user_id=current_user.id).count()
    nombre_commandes = Commande.query.filter_by(user_id=current_user.id).count()
    # Récupérer les articles de la base de données
    articles =  current_user.articles
    commandes = current_user.commande

    # Créer un dictionnaire pour stocker le nombre d'articles créés par jour
    articles_par_jour = defaultdict(int)
    for article in articles:
        # Utiliser la date de création de l'article pour grouper les articles par jour
        jour_creation = article.date_creation.date()
        articles_par_jour[jour_creation] += 1

    # Convertir le dictionnaire en listes de dates et de nombres d'articles
    dates = list(articles_par_jour.keys())
    nombres_articles = list(articles_par_jour.values())

    #Pagination
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)

    return render_template('user_dashboard/acceuil.html',dates=dates, nombres_articles=nombres_articles,nombre_articles=nombre_articles, articles_pagination=articles_pagination, nombre_commandes=nombre_commandes, articles=articles, commandes=commandes)

@app.route("/articles")
def article():
    articles = current_user.articles
    #Pagination des articles
    page = request.args.get('page', 1, type=int)
    articles_pagination = Article.query.filter_by(user_id=current_user.id).order_by(Article.id.desc()).paginate(page=page, per_page=number_articles_per_page, error_out=False)
    
    #Pagination des commandes
    commande_page = request.args.get('commandes_page', 1, type=int)
    commandes_pagination = Commande.query.filter_by(user_id=current_user.id).order_by(Commande.id.desc()).paginate(page=commande_page, per_page=number_commandes_per_page, error_out=False)

    user_commandes = Commande.query.filter_by(user_id=current_user.id).all()

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
            existing_address.rue = form_newadresse.rue.data
            existing_address.code_postal = form_newadresse.code_postal.data
            existing_address.pays = form_newadresse.pays.data
            existing_address.ville = form_newadresse.ville.data
        else:
            new_address = Adresse(
                rue=form_newadresse.rue.data,
                code_postal=form_newadresse.code_postal.data,
                pays=form_newadresse.pays.data,
                ville=form_newadresse.ville.data,
                user_id=current_user.id
            )
            db.session.add(new_address)
        db.session.commit()
        flash('Votre adresse a été ajoutée/modifiée avec succès!', 'success')
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

@app.route("/update_article_dates", methods=['GET', 'POST'])
@login_required
def update_article_dates():
    # Récupérer tous les articles de la base de données
    articles = Article.query.all()
     # Mettre à jour la date de création pour chaque article
    for article in articles:
        if article.date_creation:  # Vérifier si la date de création n'est pas nulle
            article.date_creation = datetime.now()
    # Commit des modifications à la base de données
    db.session.commit()
    flash('Dates de création des articles mises à jour avec succès!', 'success')
    return redirect(url_for('new_article')) 

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
        commande = Commande(date_commande=datetime.now(), user_id=current_user.id)  # Assuming Commande model has a date_creation field

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
        



@app.route('/details_commande/<int:commande_id>')
def details_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    return render_template('user_dashboard/details_commande.html', title='Détails de la Commande', commande=commande)


@app.route('/articles_by_day')
def articles_by_day():
    # Récupérer la date d'il y a une semaine
    start_date = datetime.now() - timedelta(days=7)

    # Récupérer les articles créés au cours de la dernière semaine
    articles = Article.query.filter(Article.date_creation >= start_date).all()

    # Créer un dictionnaire pour stocker le nombre d'articles créés par jour
    articles_by_day = {}
    for article in articles:
        day = article.date_creation.strftime('%Y-%m-%d')
        if day in articles_by_day:
            articles_by_day[day] += 1
        else:
            articles_by_day[day] = 1

    # Convertir le dictionnaire en une liste de tuples (jour, nombre d'articles)
    data = [{'day': day, 'count': count} for day, count in articles_by_day.items()]

    return jsonify(data)


from flask import jsonify

@app.route('/commandes_by_day')
def commandes_by_day():
    # Récupérer la date d'il y a une semaine
    start_date = datetime.now() - timedelta(days=7)

    # Récupérer les commandes créées au cours de la dernière semaine
    commandes = Commande.query.filter(Commande.date_commande>= start_date).all()

    # Créer un dictionnaire pour stocker le nombre de commandes créées par jour
    commandes_by_day = {}
    for commande in commandes:
        day = commande.date_commande.strftime('%Y-%m-%d')
        if day in commandes_by_day:
            commandes_by_day[day] += 1
        else:
            commandes_by_day[day] = 1

    # Convertir le dictionnaire en une liste de tuples (jour, nombre de commandes)
    data = [{'day': day, 'count': count} for day, count in commandes_by_day.items()]

    return jsonify(data)


'''@app.route('/ajouter_adresse', methods=['POST'])
def ajouter_adresse():
    rue = request.form['rue']
    code_postal = request.form['code_postal']
    pays = request.form['pays']
    ville = request.form['ville']
    # Ajoutez les données à la base de données
    nouvelle_adresse = Adresse(rue=rue, code_postal=code_postal, pays=pays, ville=ville, user_id=current_user.id)
    db.session.add(nouvelle_adresse)
    db.session.commit()
    # Renvoyez les données de l'adresse ajoutée au format JSON
    return jsonify({'rue': rue, 'code_postal': code_postal, 'pays': pays, 'ville': ville})


@app.route('/creer_commande', methods=['GET', 'POST'])
@login_required
def creer_commande():
    selected_article_ids = request.form.getlist('articles[]')
    selected_articles = Article.query.filter(Article.id.in_(selected_article_ids)).all()

    # Récupérer les autres données du formulaire
    quantite = request.form.get('quantite')
    largeur = request.form.get('largeur')
    longueur = request.form.get('longueur')
    hauteur = request.form.get('hauteur')
    poids = request.form.get('poids')
    adresse = request.form.get('adresse')
        # Créer une instance de la classe Commande avec les données récupérées
    nouvelle_commande = Commande(
        user_id=current_user.id,
        quantite=quantite,
        date_commande=datetime.now(),
        largeur=largeur,
        longueur=longueur,
        hauteur=hauteur,
        poids=poids,
        adresse=adresse,
        articles=selected_articles
    )
    # Ajouter la nouvelle commande à la session
    db.session.add(nouvelle_commande)

    # Committer les changements pour sauvegarder la commande dans la base de données
    db.session.commit()

    articles = Article.query.all()  # Récupérer tous les articles (vous pouvez ajuster cette requête selon vos besoins)

 # Rediriger vers la page list_article.html avec les articles et la nouvelle commande
    return redirect(url_for('list_article', articles=articles, commande=nouvelle_commande))'''