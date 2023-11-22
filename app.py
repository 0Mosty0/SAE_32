import pymysql
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from validate_email_address import validate_email
import re

app = Flask(__name__)

# Configuration de la base de données
app.config['MYSQL_DATABASE_USER'] = 'phpmyadmin'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'db_SAE32'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = pymysql.connect(
    host=app.config['MYSQL_DATABASE_HOST'],
    user=app.config['MYSQL_DATABASE_USER'],
    password=app.config['MYSQL_DATABASE_PASSWORD'],
    db=app.config['MYSQL_DATABASE_DB'],
)

# Fonction pour initialiser la base de données
def init_db():
    with app.app_context():
        cursor = mysql.cursor()
        with app.open_resource('schema.sql', mode='r') as f:
            for query in f.read().split(';'):
                if query.strip():
                    cursor.execute(query)

        # Ajout d'une vérification si les tables existent
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if not tables:
            mysql.commit()

# Route pour la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')


# ...

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    email_valid = True  # Par défaut, l'e-mail est considéré comme valide
    password_valid = True  # Par défaut, le mot de passe est considéré comme valide
    email_exists = False  # Par défaut, l'e-mail n'existe pas dans la base de données
    password_match = True  # Par défaut, les mots de passe correspondent

    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        confirmation_mot_de_passe = request.form.get('confirmation_mot_de_passe')

        # Validation de l'e-mail
        email_valid = validate_email(email)

        # Validation du mot de passe
        if not email_valid or len(mot_de_passe) < 8 or not re.search("[A-Z]", mot_de_passe) or not re.search("[!@#$%^&*(),.?\":{}|<>]", mot_de_passe):
            password_valid = False

        # Vérification de l'existence de l'e-mail dans la base de données
        query_check_email = 'SELECT * FROM utilisateurs WHERE email = %s'
        data_check_email = (email,)

        with mysql.cursor() as cursor:
            cursor.execute(query_check_email, data_check_email)
            if cursor.fetchone():
                email_exists = True

        # Vérification de la correspondance des mots de passe
        if mot_de_passe != confirmation_mot_de_passe:
            password_match = False

        if not email_valid or not password_valid or email_exists or not password_match:
            return render_template('signup.html', email_valid=email_valid, password_valid=password_valid, email_exists=email_exists, password_match=password_match)

        # Hash du mot de passe avant de le stocker dans la base de données
        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        # Stockage des informations dans la base de données MySQL
        query_insert_user = 'INSERT INTO utilisateurs (nom, email, mot_de_passe) VALUES (%s, %s, %s)'
        data_insert_user = (nom, email, mot_de_passe_hash)

        try:
            with mysql.cursor() as cursor:
                cursor.execute(query_insert_user, data_insert_user)
                mysql.commit()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Erreur lors de l'inscription : {e}")
            return "Erreur lors de l'inscription"

    # Si c'est une requête GET ou une soumission de formulaire invalide, afficher la page de signup
    return render_template('signup.html', email_valid=email_valid, password_valid=password_valid, email_exists=email_exists, password_match=password_match)

@app.route('/login', methods=['GET', 'POST'])
def login():
    email_not_found = False
    incorrect_password = False

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('mot_de_passe')

        query_check_user = 'SELECT * FROM utilisateurs WHERE email = %s'
        data_check_user = (email,)

        with mysql.cursor() as cursor:
            cursor.execute(query_check_user, data_check_user)
            user = cursor.fetchone()

            if user:
                # Utilisateur trouvé, vérifier le mot de passe
                if user and check_password_hash(user['mot_de_passe'], password):
                    # Mot de passe correct, connectez l'utilisateur
                    # Vous pouvez ajouter une session utilisateur ici si nécessaire
                    return redirect(url_for('index'))
                else:
                    # Mot de passe incorrect
                    incorrect_password = True
            else:
                # Adresse e-mail non trouvée
                email_not_found = True

    return render_template('login.html', email_not_found=email_not_found, incorrect_password=incorrect_password)




if __name__ == '__main__':
    init_db()
    app.run(debug=True)
