from datetime import date as dt_date
from itsdangerous import URLSafeTimedSerializer as Serializer  
from app import db, login_manager, app
from flask_login import UserMixin
import uuid


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_admin = db.Column(db.Boolean, default=False)
    nom = db.Column(db.String(20), nullable=False)
    prenom = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(20), default='default.jpg')
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.Integer, default=None)
    email = db.Column(db.String(255), unique=True, nullable=False)
    code_enregistrement = db.Column(db.String(20), default=None)
    active = db.Column(db.Boolean, default=True)  # Champ pour indiquer si le compte est actif
    # Relation entre User et Article avec backref 'user'
    articles = db.relationship('Article', backref='User', lazy=True)
    commande = db.relationship('Commande', backref='user', lazy=True)
    adresses = db.relationship('Adresse', backref='user', lazy=True)

    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token,  max_age=1800):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token,max_age=max_age)['user_id']
        except:
            return None
        return User.query.get(user_id)



    def __init__(self, is_admin, nom, prenom, adresse, image, mot_de_passe, telephone, email, code_enregistrement ):
        self.is_admin = is_admin
        self.nom = nom
        self.prenom = prenom
        self.adresse = adresse
        self.image = image 
        self.mot_de_passe = mot_de_passe
        self.telephone = telephone
        self.email = email
        self.code_enregistrement = code_enregistrement

    def __repr__(self):
        return f"User(is_admin={self.is_admin}, nom={self.nom}, prenom={self.prenom}, adresse={self.adresse}, image={self.image}, telephone={self.telephone}, email={self.email}, code_enregistrement={self.code_enregistrement})"

    def to_dict(self):
        return{
            "id": self.id,
            "is_admin": self.is_admin,
            "nom": self.nom,
            "prenom": self.prenom,
            "adresse": self.adresse,
            "image":self.image,
            "mot_de_passe": self.mot_de_passe,
            "telephone": self.telephone,
            "code_enregistrement": self.code_enregistrement
        }
association_table_article_commande = db.Table('article_commande',
    db.Column('article_id', db.Integer, db.ForeignKey('Article.id')),
    db.Column('commande_id', db.Integer, db.ForeignKey('Commande.id'))
)
class Article(db.Model):
    __tablename__ = 'Article'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('User.id'))
    sku = db.Column(db.String(30), nullable=False)
    largeur = db.Column(db.Float(precision=5), nullable=False)
    longueur = db.Column(db.Float(precision=5), nullable=False)
    hauteur = db.Column(db.Float(precision=5), nullable=False)
    poids = db.Column(db.Float(precision=5), nullable=False)
    quantite = db.Column(db.Integer(), nullable=False)
    fragile = db.Column(db.Boolean(), default=False) 
    date_creation = db.Column(db.Date,default=dt_date.today())
    commandes = db.relationship('Commande', secondary=association_table_article_commande, back_populates='articles')


    def __init__(self, user_id,sku, largeur, longueur, hauteur, poids, quantite, fragile, date_creation):
        self.user_id = user_id
        self.sku = sku
        self.largeur = largeur
        self.longueur = longueur
        self.hauteur = hauteur
        self.poids = poids
        self.quantite = quantite
        self.fragile = fragile
        self.date_creation = date_creation

    def __repr__(self):
        return f"Article(id={self.id}, sku='{self.sku}', largeur={self.largeur}, longueur={self.longueur}, hauteur={self.hauteur}, poids={self.poids}, quantite={self.quantite}, fragile={self.fragile}, date_creation={{self.date_creation}})"

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "largeur": float(self.largeur),
            "longueur": float(self.longueur),
            "hauteur": float(self.hauteur),
            "poids": float(self.poids),
            "quantite": self.quantite,
            "fragile": self.fragile
        }

class Adresse(db.Model):
    __tablename__ = 'Adresse'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer(),db.ForeignKey('User.id') , nullable=False)
    rue = db.Column(db.String(50), default=None)
    code_postal = db.Column(db.Integer(), default=None)
    pays = db.Column(db.String(50))
    ville = db.Column(db.String(50))

    def __init__(self, rue, code_postal, pays, ville,user_id):
        self.rue = rue
        self.code_postal = code_postal
        self.pays = pays
        self.ville = ville
        self.user_id = user_id

    def __repr__(self):
        return f"Adresse(id={self.id}, rue={self.rue}, code_postal={self.code_postal}, pays={self.pays}, ville={self.ville})"

    def to_dict(self):
        return {
            "id": self.id,
            "rue": self.rue,
            "code_postal": self.code_postal,
            "pays": self.pays,
            "ville": self.ville
        }

association_table_commande_conteneur = db.Table('commande_conteneur',
    db.Column('commande_id', db.Integer, db.ForeignKey('Commande.id')),
    db.Column('conteneur_id', db.Integer, db.ForeignKey('Conteneur.id'))
)


class Commande(db.Model):
    __tablename__ = 'Commande'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_creation = db.Column(db.Date, default=dt_date.today())
    numero_commande = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    status = db.Column(db.String(20), nullable=False, default='pending')  # Exemple : 'pending', 'cancelled', 'validated'
    conteneurs = db.relationship('Conteneur', secondary=association_table_commande_conteneur, back_populates='commandes')
    articles = db.relationship('Article', secondary=association_table_article_commande, back_populates='commandes')

    def __init__(self, date_creation=date_creation, user_id=None):
        self.date_creation = date_creation
        self.articles = []
        self.user_id = user_id
        self.numero_commande = self.generate_unique_numero_commande()
        
          # Générer un numéro de commande unique
    def generate_unique_numero_commande(self):
        timestamp = dt_date.today().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:6]  # Génère un identifiant unique de 6 caractères
        return f"CMD-{timestamp}-{unique_id}"
    
    def __repr__(self):
        return f"Commande(id={self.id}, date_creation={self.date_creation}, numero_commande={self.numero_commande})"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,    
            'articles': [article.to_dict() for article in self.articles],
            "date_creation": self.date_creation,
            'numero_commande': self.numero_commande
        }
class Conteneur(db.Model):
    __tablename__ = 'Conteneur'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_conteneur = db.Column(db.String(50), nullable=False)
    largeur = db.Column(db.Float(precision=2), nullable=False)
    longueur = db.Column(db.Float(precision=2), nullable=False)
    hauteur = db.Column(db.Float(precision=2), nullable=False)
    Poid_maximal = db.Column(db.Float(precision=2), nullable=False)
    quantite = db.Column(db.Integer(), nullable=False)
    prix = db.Column(db.Float(), nullable=False)
    date_creation = db.Column(db.Date, default=dt_date.today())
    commandes = db.relationship('Commande', secondary=association_table_commande_conteneur, back_populates='conteneurs')

    

    def __init__(self,type_conteneur, longueur, largeur, Poid_maximal, hauteur, prix, quantite, date_creation):
        self.type_conteneur = type_conteneur
        self.longueur = longueur
        self.largeur = largeur
        self.Poid_maximal = Poid_maximal
        self.hauteur = hauteur
        self.prix = prix
        self.quantite = quantite
        self.date_creation = date_creation

    def __repr__(self):
        return f"Conteneur(IdContaineur={self.id}, TypeContaineur={self.type_conteneur}, Longeur={self.longueur}, Largeur={self.largeur}, PoidMaximal={self.Poid_maximal}, hauteur={self.hauteur}, prix={self.prix}, quantite={self.quantite}, date_creation={self.date_creation})"

    def to_dict(self):
        return {
            "id": self.id,
            "type_conteneur": self.type_conteneur,
            "Longueur": self.longueur,
            "Largeur": self.largeur,
            "PoidMaximal": self.Poid_maximal,
            "hauteur": self.hauteur,
            "prix": self.prix,
            "quantite": self.quantite,
            "date_creation": self.date_creation,
        }



    
'''class Paiement(db.Model):
    __tablename__ = 'Paiement'
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float)
    methode = db.Column(db.String(50))
    status = db.Column(db.String(50))
    commande = db.relationship('Commande', back_populates='paiement')

    def __init__(self, montant, methode, status):
        self.montant = montant
        self.methode = methode
        self.status = status

    def __repr__(self):
        return f"Paiement(id={self.id}, montant={self.montant}, methode={self.methode}, status={self.status})"

    def to_dict(self):
        return {
            "id": self.id,
            "montant": self.montant,
            "methode": self.methode,
            "status": self.status
        }'''
    
'''class Admin(db.Model):
    __tablename__ = 'Admin'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Integer(), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(100))
    conteneur = db.relationship('Conteneur', backref='admin',lazy=True)

    def __init__(self, nom, email, motDePasse):
        self.nom = nom
        self.email = email
        self.motDePasse = motDePasse

    def __repr__(self):
        return f"Admin(id={self.id}, nom={self.nom}, login={self.email})"

    def to_dict(self):
        return {
            "idAdmin": self.idAdmin,
            "nom": self.nom,
            "login": self.email
        }'''


'''class AlgorithmeBinPacking(db.Model):
    __tablename__ = 'AlgorithmeBinPacking'
    id = db.Column(db.Integer, primary_key=True)
    list_conteneur = db.Column(db.List())
    list_article = db.Column(db.List())
    conteneur = db.relationship('Conteneur', backref='algorithme_bin_packing')
  )

    def __init__(self, conteneur, article):
        self.conteneur = conteneur
        self.article = article

    def __repr__(self):
        return f"AlgorithmeBinPacking(conteneur={self.conteneur}, article={self.article})"

    def to_dict(self):
        return {
            "conteneur": self.conteneur.to_dict(),
            "article": self.article.to_dict()
        }'''
