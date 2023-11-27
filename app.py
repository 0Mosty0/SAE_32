from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email_address import validate_email
import re
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from functools import wraps

app = Flask(__name__)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://phpmyadmin:root@127.0.0.1:3306/db_SAE32'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Définition de la classe Utilisateur
class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    mot_de_passe = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), default='user')
    adresse = db.Column(db.Text, nullable=True)
    codePostal = db.Column(db.Text, nullable=True)
    ville = db.Column(db.Text, nullable=True)
    tel = db.Column(db.Text, nullable=True)


# Définition de la classe Colis
class Colis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poids = db.Column(db.Integer)
    hauteur = db.Column(db.Integer)
    largeur = db.Column(db.Integer)
    longueur = db.Column(db.Integer)
    etat = db.Column(db.String(20))
    dateEmballage = db.Column(db.Date)
    dateArriveDepot = db.Column(db.Date)
    dateDepartDepot = db.Column(db.Date)
    dateLivraison = db.Column(db.Date)
    dateReception = db.Column(db.Date)
    expediteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    transporteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    destinataire_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))

    # Définir les relations avec les utilisateurs
    expediteur = db.relationship('Utilisateur', foreign_keys=[expediteur_id])
    transporteur = db.relationship('Utilisateur', foreign_keys=[transporteur_id])
    destinataire = db.relationship('Utilisateur', foreign_keys=[destinataire_id])



# Secret key for session management
app.secret_key = 'your_secret_key'

# Set up logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, 'site.log')
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)  # Niveau INFO pour site.log
app.logger.addHandler(handler)

login_log_file = os.path.join(logs_dir, 'tentative_login.log')
login_handler = RotatingFileHandler(login_log_file, maxBytes=10000, backupCount=1)
login_handler.setLevel(logging.WARNING)  # Niveau WARNING pour tentative_login.log
login_logger = logging.getLogger('tentative_login')
login_logger.addHandler(login_handler)

# Decorator to check if the user has admin rights
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' in session and session.get('role') in roles:
                return f(*args, **kwargs)
            else:
                flash("Vous n'avez pas les droits nécessaires pour accéder à cette page.", 'danger')
                app.logger.info(f"Unauthorized access to {roles} page by user: {session.get('email')}")
                return redirect(url_for('unauthorized'))
        return decorated_function
    return decorator

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

# app.py

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        confirmation_mot_de_passe = request.form.get('confirmation_mot_de_passe')
        adresse = request.form.get('adresse')
        codePostal = request.form.get('codePostal')
        ville = request.form.get('ville')
        tel = request.form.get('tel')

        email_valid = validate_email(email)

        if not email_valid or len(mot_de_passe) < 8 or not re.search("[A-Z]", mot_de_passe) or not re.search("[!@#$%^&*(),.?\":{}|<>]", mot_de_passe):
            flash("Veuillez saisir une adresse e-mail valide et un mot de passe fort.", 'danger')
            return render_template('signup.html', email_valid=email_valid)

        # Vérifier si l'e-mail existe déjà
        existing_user = Utilisateur.query.filter_by(email=email).first()
        if existing_user:
            flash("L'adresse e-mail existe déjà.", 'danger')
            return render_template('signup.html', email_valid=email_valid)

        if mot_de_passe != confirmation_mot_de_passe:
            flash("Les mots de passe ne correspondent pas.", 'danger')
            return render_template('signup.html', email_valid=email_valid)

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        # Insérer l'utilisateur dans la base de données
        new_user = Utilisateur(
            nom=nom, email=email, mot_de_passe=mot_de_passe_hash,
            adresse=adresse, codePostal=codePostal, ville=ville, tel=tel
        )
        db.session.add(new_user)

        try:
            db.session.commit()
            flash("Inscription réussie. Vous pouvez maintenant vous connecter.", 'success')
            app.logger.info(f"New user registered: {email}")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            error_message = f"Erreur lors de l'inscription : {e}"
            print(error_message)
            app.logger.error(error_message)
            flash("Erreur lors de l'inscription.", 'danger')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_messages = []

    # Vérifier si l'utilisateur est déjà connecté
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('mot_de_passe')

        # Vérifier l'existence de l'utilisateur et la validité du mot de passe
        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and check_password_hash(utilisateur.mot_de_passe, password):
            # Connexion réussie, enregistrez les informations de session
            session['loggedin'] = True
            session['id'] = utilisateur.id
            session['nom'] = utilisateur.nom
            session['email'] = utilisateur.email
            session['role'] = utilisateur.role  # Ajout du rôle dans la session
            app.logger.info(f"User logged in: {email}")
            return redirect(url_for('dashboard'))
        else:
            error_messages.append("Adresse e-mail ou mot de passe incorrects.")
            log_message = f"Tentative de connexion échouée pour l'utilisateur {email} depuis l'IP {request.remote_addr} à {datetime.now(pytz.timezone('Europe/Paris')).strftime('%Y-%m-%d %H:%M:%S')}"
            login_logger.warning(log_message)  # Utiliser le nouveau logger
            with open(login_log_file, 'a') as login_log:
                login_log.write(log_message + '\n')

    # Passer les messages d'erreur directement au template
    return render_template('login.html', error_messages=error_messages)

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        user_id = session.get('id')

        # Vérifiez si l'ID de l'utilisateur est présent dans la session
        if user_id:
            # Récupérer les informations de l'utilisateur depuis la base de données
            utilisateur = Utilisateur.query.get(user_id)

            # Vérifier si l'utilisateur existe
            if utilisateur:
                nom = utilisateur.nom
                email = utilisateur.email
                role = utilisateur.role
                adresse = utilisateur.adresse
                codePostal = utilisateur.codePostal
                ville = utilisateur.ville
                tel = utilisateur.tel
            else:
                flash("Aucune information de l'utilisateur trouvée.", 'danger')
                return redirect(url_for('login'))

            return render_template('dashboard.html', nom=nom, email=email, role=role, adresse=adresse, codePostal=codePostal, ville=ville, tel=tel)
        else:
            flash("Erreur lors de la récupération des informations de l'utilisateur.", 'danger')
            return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'loggedin' in session:
        app.logger.info(f"User logged out: {session.get('email')}")
    session.clear()
    flash("Vous avez été déconnecté avec succès.", 'success')
    return redirect(url_for('login'))


@app.route('/mes_colis')
@role_required('admin', 'user')
def mes_colis():
    return 'Bienvenue dans l\'espace de tes colis!'

@app.route('/expediteur')
@role_required('admin', 'expediteur')
def expediteur():
    transporteurs = Utilisateur.query.filter_by(role='transporteur').all()
    destinataires = Utilisateur.query.all()

    if request.method == 'POST':
        poids = request.form.get('poids')
        hauteur = request.form.get('hauteur')
        largeur = request.form.get('largeur')
        longueur = request.form.get('longueur')
        transporteur_id = request.form.get('transporteur_id')
        destinataire_id = request.form.get('destinataire_id')

        # Vérifier que les champs obligatoires sont renseignés
        if not poids or not hauteur or not largeur or not longueur or not transporteur_id or not destinataire_id:
            flash("Veuillez remplir tous les champs obligatoires.", 'danger')
            return render_template('expediteur.html', transporteurs=transporteurs, destinataires=destinataires)

        # Créer une instance de Colis
        nouveau_colis = Colis(
            poids=poids,
            hauteur=hauteur,
            largeur=largeur,
            longueur=longueur,
            etat='En attente',
            dateEmballage=datetime.now().date(),
            expediteur_id=session['id'],
            transporteur_id=transporteur_id,
            destinataire_id=destinataire_id
        )

        # Ajouter le colis à la base de données
        db.session.add(nouveau_colis)

        try:
            db.session.commit()
            flash("Le colis a été créé avec succès.", 'success')
            return redirect(url_for('mes_colis'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création du colis : {e}", 'danger')

    return render_template('expediteur.html', transporteurs=transporteurs, destinataires=destinataires)


@app.route('/transporteur')
@role_required('admin', 'transporteur')
def transporteur():
    return 'Bienvenue dans l\'espace transporteur !'

@app.route('/admin')
@role_required('admin')
def admin():
    return 'Bienvenue dans l\'espace admin !'


if __name__ == '__main__':
    app.run(debug=True)