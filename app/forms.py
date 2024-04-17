from flask_bcrypt import check_password_hash
from flask_login import current_user
from flask_wtf import FlaskForm
import re
from wtforms import DateField, DateTimeField, FloatField, HiddenField, IntegerField, SelectField, SelectMultipleField, StringField, PasswordField, SubmitField, BooleanField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    nom = StringField('nom', validators=[DataRequired(), Length(min=2, max=20)])
    prenom = StringField('prenom', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('email', validators=[DataRequired(), Email()])
    mot_de_passe = PasswordField('Mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('mot_de_passe', message='Les mots de passe ne correspondent pas')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
        
    def validate_mot_de_passe(form, field):
        mot_de_passe = field.data
        if len(mot_de_passe) < 8:
            raise ValidationError('Le mot de passe doit contenir au moins 8 caractères, inclure des lettres, des chiffres et des caractères spéciaux.')
        if not re.search(r'[a-zA-Z]', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des lettres')
        if not re.search(r'\d', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des chiffres')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_-]', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des caractères spéciaux')
        

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()])
    mot_de_passe = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    nom = StringField('Nom', validators=[])
    prenom = StringField('Prenom', validators=[])
    email = StringField('Email', validators=[Email()])
    image = FileField(' ', validators=[FileAllowed(['jpg', 'png'])])
    telephone = IntegerField('Téléphone', validators=[])
    submit = SubmitField('Metre à jour')

            
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
            
            

class Updatepassword(FlaskForm):
    mot_de_passe = PasswordField('Nouveau mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer mot de passe', validators=[DataRequired(), EqualTo('mot_de_passe', message='Les mots de passe ne correspondent pas')])
    submit = SubmitField('Changer mot de passe')

    def validate_mot_de_passe(self, mot_de_passe):
        if mot_de_passe.data and check_password_hash(current_user.mot_de_passe, mot_de_passe.data):
            raise ValidationError("Le nouveau mot de passe doit être différent de l'ancien.")
        if len(mot_de_passe.data) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>_-])(?=.*[a-zA-Z0-9]).{8,}$', mot_de_passe.data):
            raise ValidationError('Le mot de passe doit contenir au moins 8 caractères, inclure des lettres, des chiffres et des caractères spéciaux.')
    

class ArticleForm(FlaskForm):
    id = HiddenField('ID de l\'article')
    sku = SelectField('Sku/Id', validators=[DataRequired()], choices=[
        ('conteneur', 'Conteneur'),
        ('caisse', 'Caisse'),
        ('pallet', 'Pallet'),
        ('carton', 'Carton')
    ])
    largeur = FloatField('Largeur', validators=[DataRequired()],render_kw={"placeholder": "Cm"}) 
    longueur = FloatField('Longeur', validators=[DataRequired()],render_kw={"placeholder": "Cm"})
    hauteur = FloatField('Hauteur', validators=[DataRequired()],render_kw={"placeholder": "Cm"})
    poids = FloatField('Poids', validators=[DataRequired()],render_kw={"placeholder": "Kg"})
    quantite = IntegerField('Quantité', validators=[DataRequired()])
    fragile = BooleanField('Fragile', default=False)
    submit = SubmitField('Ajouter')

class UpdateArticleForm(FlaskForm):
    id = HiddenField('ID de l\'article')
    sku = StringField('Sku/Id')
    largeur = FloatField('Largeur')
    longueur = FloatField('Longeur')
    hauteur = FloatField('Hauteur')
    poids = FloatField('Poids')
    quantite = IntegerField('Quantité')
    fragile = BooleanField('Fragile')
    submit = SubmitField('Mettre à jour')

class RequestResetForm(FlaskForm):
    email = StringField('Adress email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Changé mot de passe')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')
        
class ResetPasswordForm(FlaskForm):
    mot_de_passe = PasswordField('Entrez votre nouveau mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmé votre nouveau mot de passe', validators=[DataRequired(), EqualTo('mot_de_passe', message='Les mots de passe ne correspondent pas')])
    submit = SubmitField('Confirmer')

    def validate_mot_de_passe(form, field):
        mot_de_passe = field.data
        if len(mot_de_passe) < 8:
            raise ValidationError('Le mot de passe doit contenir au moins 8 caractères, inclure des lettres, des chiffres et des caractères spéciaux.')
        if not re.search(r'[a-zA-Z]', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des lettres')
        if not re.search(r'\d', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des chiffres')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_-]', mot_de_passe):
            raise ValidationError('Le mot de passe doit contenir des caractères spéciaux')
        
class AjouterAdress(FlaskForm):
    id = HiddenField('ID de l\'adresse')
    rue = StringField('rue')
    code_postal = IntegerField('code postal')
    pays = StringField('Pays')
    ville = StringField('ville')
    submit = SubmitField('Ajouter')


class CommandeForm(FlaskForm):
    id = HiddenField("iD de la commande")
    date_commade = DateTimeField("Date Commande")
    numero_commande = StringField("N° commande")
    articles = SelectMultipleField('Articles', coerce=int, validators=[DataRequired()])


    
'''class CommandeForm(FlaskForm):
    quantite = IntegerField('Quantité', validators=[DataRequired()])
    largeur = FloatField('Largeur', validators=[DataRequired()])
    longueur = FloatField('Longueur', validators=[DataRequired()])
    hauteur = FloatField('Hauteur', validators=[DataRequired()])
    poids = FloatField('Poids', validators=[DataRequired()])
    adresse = StringField('Adresse', validators=[DataRequired()])
    date_creation = DateField('Date Commande', validators=[DataRequired()])
    submit = SubmitField('Créer Commande')'''
