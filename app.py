from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email_address import validate_email
import re
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import pytz
from functools import wraps
from geopy.geocoders import Nominatim


app = Flask(__name__)
# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://phpmyadmin:root@127.0.0.1:3306/db_SAE32'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'your_secret_key'

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom, email, mot_de_passe = db.Column(db.Text, nullable=False), db.Column(db.Text, nullable=False, unique=True), db.Column(db.Text, nullable=False)
    role, adresse, codePostal, ville, tel = db.Column(db.String(50), default='user'), db.Column(db.Text, nullable=True), db.Column(db.Text, nullable=True), db.Column(db.Text, nullable=True), db.Column(db.Text, nullable=True)
    vehicules = db.relationship('Vehicule', back_populates='transporteur', lazy=True)

class Colis(db.Model):
    id, poids, hauteur, largeur, longueur, etat = db.Column(db.Integer, primary_key=True), db.Column(db.Integer), db.Column(db.Integer), db.Column(db.Integer), db.Column(db.Integer), db.Column(db.String(20))
    dateEmballage, dateArriveDepot, dateDepartDepot, dateLivraison, dateReception = db.Column(db.Date), db.Column(db.Date), db.Column(db.Date), db.Column(db.Date), db.Column(db.Date)
    expediteur_id, transporteur_id, destinataire_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id')), db.Column(db.Integer, db.ForeignKey('utilisateur.id')), db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    expediteur, adresse, ville, transporteur, destinataire = db.relationship('Utilisateur', foreign_keys=[expediteur_id]), db.relationship('Utilisateur', foreign_keys=[expediteur_id]), db.relationship('Utilisateur', foreign_keys=[expediteur_id]), db.relationship('Utilisateur', foreign_keys=[transporteur_id]), db.relationship('Utilisateur', foreign_keys=[destinataire_id])
    vehicules = db.relationship('Vehicule', secondary='colisvehiculeassociation', back_populates='colis')
    latitude = db.Column(db.DECIMAL(10, 8), default=None)
    longitude = db.Column(db.DECIMAL(11, 8), default=None)

class Vehicule(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    marque = db.Column(db.String(50), nullable=False)
    modele = db.Column(db.String(50), nullable=False)
    annee_fabrication = db.Column(db.Integer)
    immatriculation = db.Column(db.String(20), unique=True, nullable=False)
    latitude = db.Column(db.DECIMAL(10, 8), default=None)
    longitude = db.Column(db.DECIMAL(11, 8), default=None)
    en_livraison = db.Column(db.Boolean, default=False)
    transporteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    transporteur = db.relationship('Utilisateur', back_populates='vehicules', lazy=True)
    colis = db.relationship('Colis', secondary='colisvehiculeassociation', back_populates='vehicules')

class ColisVehiculeAssociation(db.Model):
    __tablename__ = 'colisvehiculeassociation'
    colis_id, vehicule_id = db.Column(db.Integer, db.ForeignKey('colis.id'), primary_key=True), db.Column(db.Integer, db.ForeignKey('vehicule.id'), primary_key=True)
    colis, vehicule = db.relationship('Colis', overlaps="colis,vehicules"), db.relationship('Vehicule', overlaps="colis,vehicules")

logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, 'site.log')
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

login_log_file = os.path.join(logs_dir, 'tentative_login.log')
login_handler = RotatingFileHandler(login_log_file, maxBytes=10000, backupCount=1)
login_handler.setLevel(logging.WARNING)
login_logger = logging.getLogger('tentative_login')
login_logger.addHandler(login_handler)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' in session and session.get('role') in roles:
                return f(*args, **kwargs)
            else:
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Vérifier si l'utilisateur est déjà connecté
    if 'loggedin' in session:
        return redirect(url_for('index'))
    
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
            return render_template('signup.html', email_valid=email_valid)

        # Vérifier si l'e-mail existe déjà
        existing_user = Utilisateur.query.filter_by(email=email).first()
        if existing_user:
            return render_template('signup.html', email_valid=email_valid)

        if mot_de_passe != confirmation_mot_de_passe:
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
            app.logger.info(f"New user registered: {email}")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            error_message = f"Erreur lors de l'inscription : {e}"
            print(error_message)
            app.logger.error(error_message)

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_messages = []

    # Vérifier si l'utilisateur est déjà connecté
    if 'loggedin' in session:
        return redirect(url_for('index'))

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
            return redirect(url_for('index'))
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
                return redirect(url_for('login'))

            return render_template('dashboard.html', nom=nom, email=email, role=role, adresse=adresse, codePostal=codePostal, ville=ville, tel=tel)
        else:
            return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'loggedin' in session:
        app.logger.info(f"User logged out: {session.get('email')}")
    session.clear()
    return redirect(url_for('login'))


@app.route('/suivi_colis', methods=['GET', 'POST'])
def suivi_colis():
    if request.method == 'POST':
        # Récupérer l'ID du colis à partir du formulaire
        colis_id = request.form.get('colis_id')

        # Récupérer les informations du colis depuis la base de données
        colis = Colis.query.get(colis_id)

        if colis:
            # Vous pouvez transmettre ces informations à la page HTML pour les afficher
            return render_template('suivi_colis.html', colis=colis)
        

    return render_template('suivi_colis.html')


@app.route('/expediteur', methods=['GET', 'POST'])
@role_required('admin', 'expediteur')
def expediteur():
    transporteurs = Utilisateur.query.filter_by(role='transporteur').all()
    destinataires = Utilisateur.query.filter_by(role='user').all()
    expediteurs = None
    latitude = None
    longitude = None

    user_id = session.get('id', None)
    expediteur_id = user_id

    if session.get('role') == 'admin':
        expediteurs = Utilisateur.query.filter_by(role='expediteur').all()
        expediteur_id = request.form.get('expediteur_id') or expediteur_id

    expediteur = Utilisateur.query.get(expediteur_id)
    adresse_expediteur = expediteur.adresse + ", " + expediteur.ville + " " + expediteur.codePostal + " " + "France"

    geolocator = Nominatim(user_agent="votre_application")
    location = geolocator.geocode(adresse_expediteur, addressdetails=True)

    if location:
        latitude, longitude = location.latitude, location.longitude
    else:
        return render_template('expediteur.html', transporteurs=transporteurs, destinataires=destinataires, expediteurs=expediteurs)

    if request.method == 'POST':
        poids = request.form.get('poids')
        hauteur = request.form.get('hauteur')
        largeur = request.form.get('largeur')
        longueur = request.form.get('longueur')
        transporteur_id = request.form.get('transporteur_id')
        destinataire_id = request.form.get('destinataire_id')

        nouveau_colis = Colis(
            poids=poids,
            hauteur=hauteur,
            largeur=largeur,
            longueur=longueur,
            etat='En attente',
            dateEmballage=datetime.now().date(),
            expediteur_id=expediteur_id,
            transporteur_id=transporteur_id,
            destinataire_id=destinataire_id,
            latitude=latitude,
            longitude=longitude
        )

        db.session.add(nouveau_colis)

        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()

    return render_template('expediteur.html', transporteurs=transporteurs, destinataires=destinataires, expediteurs=expediteurs)

# Nouvelle route pour la gestion des véhicules
@app.route('/vehicule', methods=['GET', 'POST'])
@role_required('admin', 'transporteur')
def gestion_vehicules():
    if request.method == 'POST':
        # Récupérer les données du formulaire d'ajout de véhicule
        marque = request.form.get('marque')
        modele = request.form.get('modele')
        annee_fabrication = request.form.get('annee_fabrication')
        immatriculation = request.form.get('immatriculation')
        transporteur_id = request.form.get('transporteur_id')  # Nouveau champ pour l'ID du transporteur

        # Vérifier que tous les champs sont renseignés
        if not marque or not modele or not annee_fabrication or not immatriculation or not transporteur_id:
            return redirect(url_for('gestion_vehicules'))

        # Créer une instance de Vehicule et l'associer au transporteur
        nouveau_vehicule = Vehicule(
            marque=marque,
            modele=modele,
            annee_fabrication=annee_fabrication,
            immatriculation=immatriculation,
            transporteur_id=transporteur_id
        )

        # Ajouter le véhicule à la base de données
        db.session.add(nouveau_vehicule)

        try:
            # Récupérer l'adresse du transporteur
            transporteur = Utilisateur.query.filter_by(id=transporteur_id).first()
            adresse_transporteur = f"{transporteur.adresse}, {transporteur.ville} {transporteur.codePostal} France"

            # Utiliser le service de géocodage pour obtenir les coordonnées
            geolocator = Nominatim(user_agent="geoapi")
            location = geolocator.geocode(adresse_transporteur)

            # Mettre à jour la position GPS du nouveau véhicule
            if location:
                nouveau_vehicule.latitude = location.latitude
                nouveau_vehicule.longitude = location.longitude

            db.session.commit()
        except Exception as e:
            db.session.rollback()

    if session.get('role') == 'admin':
        vehicules = db.session.query(Vehicule, Utilisateur).join(Utilisateur).all()
        transporteurs = Utilisateur.query.filter_by(role='transporteur').all()
    else:
        transporteur_id = session.get('id')
        vehicules = Vehicule.query.filter_by(transporteur_id=transporteur_id).all()
        transporteurs = None  # L'utilisateur non-admin n'a pas besoin de voir la liste des transporteurs

    return render_template('vehicule.html', vehicules=vehicules, transporteurs=transporteurs)

@app.route('/supprimer_vehicule/<int:vehicule_id>', methods=['POST'])
@role_required('admin', 'transporteur')
def supprimer_vehicule(vehicule_id):
    vehicule = Vehicule.query.get_or_404(vehicule_id)

    if not vehicule.en_livraison:
        db.session.delete(vehicule)
        db.session.commit()
    
    return redirect(url_for('gestion_vehicules'))


@app.route('/prepare_livraison', methods=['GET', 'POST'])
@role_required('admin', 'transporteur')
def prepare_livraison():
    # Récupérer le rôle de l'utilisateur connecté depuis la session
    role = session.get('role')
    # Récupérer l'ID du transporteur depuis la session
    transporteur_id = session['id']

    if request.method == 'POST':
        vehicule_id = request.form['vehicule_id']
        colis_ids = request.form.getlist('colis_ids')
        annuler_livraison = 'annuler_livraison' in request.form

        try:
            vehicule = Vehicule.query.get(vehicule_id)

            for colis_id in colis_ids:
                colis = Colis.query.get(colis_id)

                if annuler_livraison:
                    # Annuler la livraison : réinitialiser les coordonnées du colis à l'adresse du transporteur
                    geolocator = Nominatim(user_agent="my_geocoder")
                    location = geolocator.geocode(f"{colis.expediteur.adresse}, {colis.expediteur.ville}")

                    if location:
                        colis.latitude = location.latitude
                        colis.longitude = location.longitude
                        colis.etat = "En attente"
                        colis.dateArriveDepot = None
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    # Préparer la livraison : mettre à jour les coordonnées du colis avec celles du véhicule
                    colis.latitude = vehicule.latitude
                    colis.longitude = vehicule.longitude
                    colis.etat = "Au dépôt"
                    colis.dateArriveDepot = datetime.now().date()

                # Ajouter le colis au véhicule
                vehicule.colis.append(colis)

            db.session.commit()
            return redirect(url_for('prepare_livraison'))

        except Exception as e:
            db.session.rollback()
            return redirect(url_for('dashboard'))

    else:
        # Récupérer la liste des véhicules
        if role == "admin":
            vehicules = Vehicule.query.all()
        else:  # Si c'est un transporteur, récupérer uniquement les véhicules qui lui sont attribués
            vehicules = Vehicule.query.filter_by(transporteur_id=transporteur_id).all()

        # Récupérer la liste des colis non livrés
        colis_non_livres = Colis.query.filter_by(etat="En attente").all()

        # Si c'est un transporteur, récupérer uniquement les colis qui lui sont attribués
        if role == "transporteur":
            colis_prepared = Colis.query.join(ColisVehiculeAssociation).join(Vehicule).filter(Vehicule.transporteur_id == transporteur_id, Colis.etat == "Au dépôt").all()
        else:
            colis_prepared = Colis.query.filter_by(etat="Au dépôt").all()

        return render_template('prepare_livraison.html', vehicules=vehicules, colis_non_livres=colis_non_livres, colis_prepared=colis_prepared)


@app.route('/annuler_livraison/<int:colis_id>', methods=['POST'])
@role_required('admin', 'transporteur')
def annuler_livraison(colis_id):
    # Mettre le colis "En attente" et dissocier de son véhicule
    colis = Colis.query.get(colis_id)
    if colis:
        # Recherche de l'association dans la table colisvehiculeassociation
        association = ColisVehiculeAssociation.query.filter_by(colis_id=colis_id).first()
        if association:
            # Suppression de l'association de la table
            db.session.delete(association)
        colis.etat = "En attente"
        db.session.commit()
    return redirect(url_for('prepare_livraison'))

@app.route('/envoyer_vehicule/<int:vehicule_id>', methods=['POST'])
@role_required('admin', 'transporteur')
def envoyer_vehicule(vehicule_id):
    # Mettre à jour la dateDepartDepot et l'état des colis associés au véhicule
    vehicule = Vehicule.query.get(vehicule_id)
    if vehicule:
        for colis in vehicule.colis:
            colis.dateDepartDepot = datetime.now().date()
            colis.etat = "En Livraison"
        vehicule.en_livraison = True
        db.session.commit()
    return redirect(url_for('prepare_livraison'))


import requests

@app.route('/livraisons_en_cours', methods=['GET', 'POST'])
@role_required('admin', 'transporteur')
def livraisons_en_cours():
    # Assurez-vous que l'utilisateur est authentifié et est un livreur ou un admin
    if 'id' not in session or 'role' not in session or session['role'] not in ['transporteur', 'admin']:
        # Rediriger ou afficher un message d'erreur selon votre logique
        return redirect(url_for('unauthorized'))

    # Récupérer tous les véhicules en cours de livraison
    vehicules_en_cours = (
        db.session.query(Vehicule)
        .join(ColisVehiculeAssociation, Vehicule.id == ColisVehiculeAssociation.vehicule_id)
        .join(Colis, ColisVehiculeAssociation.colis_id == Colis.id)
        .filter(Colis.etat == "En Livraison")
        .distinct()
        .all()
    )

    # Récupérer tous les colis en cours de livraison classés par véhicule
    colis_par_vehicule = {}
    for vehicule in vehicules_en_cours:
        colis_par_vehicule[vehicule] = (
            db.session.query(Colis, ColisVehiculeAssociation)
            .join(ColisVehiculeAssociation)
            .filter(Colis.etat == "En Livraison", ColisVehiculeAssociation.vehicule_id == vehicule.id)
            .all()
        )

    if request.method == 'POST':
        # Récupérer les identifiants des colis marqués comme "Livrés" depuis le formulaire
        colis_livres_ids = request.form.getlist('colis_livre')

        # Mettre à jour le statut des colis marqués comme "Livrés"
        for vehicule, colis_assoc_list in colis_par_vehicule.items():
            for colis, assoc in colis_assoc_list:
                if str(colis.id) in colis_livres_ids:
                    # Supprimer l'association entre le colis et le véhicule
                    db.session.delete(assoc)

                    # Mettre à jour le statut du colis
                    colis.etat = "Livrée"
                    colis.dateLivraison = datetime.now()

                    # Obtenir les coordonnées à partir de l'adresse du destinataire
                    adresse_destinataire = colis.destinataire.adresse + ", " + colis.destinataire.ville + " " + colis.destinataire.codePostal + " " + "France"

                    coords_destinataire = geocode(adresse_destinataire)

                    if coords_destinataire:
                        colis.latitude, colis.longitude = coords_destinataire

                    # Si le véhicule n'a plus de colis, mettre à jour son statut
                    if not vehicule.colis:
                        vehicule.en_livraison = False

        db.session.commit()
        return redirect(url_for('livraisons_en_cours'))

    return render_template('livraisons_en_cours.html', colis_par_vehicule=colis_par_vehicule)

def geocode(adresse):
    """
    Utilise un service de géocodage pour obtenir les coordonnées à partir d'une adresse.
    """
    # Utilisez l'API de géocodage de votre choix (exemple : Nominatim de OpenStreetMap)
    geocoding_api = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': adresse,
        'format': 'json'
    }

    response = requests.get(geocoding_api, params=params)
    data = response.json()

    if data:
        first_result = data[0]
        latitude = float(first_result['lat'])
        longitude = float(first_result['lon'])
        return latitude, longitude
    else:
        return None


@app.route('/mes_colis', methods=['GET', 'POST'])
@role_required('admin', 'user', 'transporteur', 'expediteur')
def mes_colis():
    # Récupérer le rôle de l'utilisateur connecté depuis la session
    role = session.get('role')

    if request.method == 'POST':
        colis_id_reception = request.form.get('confirmer_reception_colis_id')
        if colis_id_reception:
            # Mettre à jour le statut du colis si le colis est "Livrée"
            colis = Colis.query.get(colis_id_reception)
            if colis and colis.etat == "Livrée":
                colis.etat = "Reçue"
                colis.dateReception = datetime.now().date()
                db.session.commit()

    if role == 'admin':
        # Si l'utilisateur est un administrateur, récupérer tous les colis
        colis_destinataire = Colis.query.all()
    else:
        # Sinon, récupérer l'ID du destinataire depuis la session
        destinataire_id = session['id']
        # Récupérer la liste des colis du destinataire
        colis_destinataire = Colis.query.filter_by(destinataire_id=destinataire_id).all()

    # Récupérer les coordonnées des colis qui ne sont pas "Livrée"
    colis_non_livres_coords = [
        {'id': colis.id, 'latitude': colis.latitude, 'longitude': colis.longitude}
        for colis in colis_destinataire
        if colis.etat != "Reçue" and colis.latitude is not None and colis.longitude is not None
    ]

    return render_template('mes_colis.html', colis_destinataire=colis_destinataire, colis_non_livres_coords=colis_non_livres_coords)

# Démarrer l'application si le fichier est exécuté directement
if __name__ == '__main__':
    app.run(debug=True, port=3456)

