import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email_address import validate_email
import re

app = Flask(__name__)

# Configuration de la base de données
mysql_config = {
    'host': '127.0.0.1',
    'user': 'phpmyadmin',
    'password': 'root',
    'database': 'db_SAE32',
    'port': 3306,
}

# Connexion à la base de données MySQL
mysql = pymysql.connect(**mysql_config)

# Secret key for session management
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        confirmation_mot_de_passe = request.form.get('confirmation_mot_de_passe')

        email_valid = validate_email(email)

        if not email_valid or len(mot_de_passe) < 8 or not re.search("[A-Z]", mot_de_passe) or not re.search("[!@#$%^&*(),.?\":{}|<>]", mot_de_passe):
            flash("Veuillez saisir une adresse e-mail valide et un mot de passe fort.", 'danger')
            return render_template('signup.html', email_valid=email_valid)

        # Vérifier si l'e-mail existe déjà
        with mysql.cursor() as cursor:
            try:
                cursor.execute('SELECT * FROM utilisateurs WHERE email = %s', (email,))
                if cursor.fetchone():
                    flash("L'adresse e-mail existe déjà.", 'danger')
                    return render_template('signup.html', email_valid=email_valid)
            except pymysql.Error as e:
                print(f"Erreur lors de la vérification de l'e-mail existant : {e}")
                flash("Erreur lors de la vérification de l'e-mail existant.", 'danger')
                return render_template('signup.html', email_valid=email_valid)

        if mot_de_passe != confirmation_mot_de_passe:
            flash("Les mots de passe ne correspondent pas.", 'danger')
            return render_template('signup.html', email_valid=email_valid)

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        # Insérer l'utilisateur dans la base de données
        query_insert_user = 'INSERT INTO utilisateurs (nom, email, mot_de_passe) VALUES (%s, %s, %s)'
        data_insert_user = (nom, email, mot_de_passe_hash)

        with mysql.cursor() as cursor:
            try:
                cursor.execute(query_insert_user, data_insert_user)
                mysql.commit()
                flash("Inscription réussie. Vous pouvez maintenant vous connecter.", 'success')
                return redirect(url_for('login'))
            except pymysql.Error as e:
                print(f"Erreur lors de l'inscription : {e}")
                flash("Erreur lors de l'inscription.", 'danger')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_messages = []

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('mot_de_passe')

        # Vérifier l'existence de l'utilisateur et la validité du mot de passe
        with mysql.cursor() as cursor:
            try:
                cursor.execute('SELECT * FROM utilisateurs WHERE email = %s', (email,))
                utilisateur = cursor.fetchone()

                if utilisateur and check_password_hash(utilisateur[3], password):
                    # Connexion réussie, enregistrez les informations de session
                    session['loggedin'] = True
                    session['id'] = utilisateur[0]
                    session['nom'] = utilisateur[1]
                    session['email'] = utilisateur[2]
                    return redirect(url_for('dashboard'))
                else:
                    error_messages.append("Adresse e-mail ou mot de passe incorrects.")

            except pymysql.Error as e:
                print(f"Erreur lors de la connexion : {e}")
                error_messages.append("Erreur lors de la connexion.")

    # Passer les messages d'erreur directement au template
    return render_template('login.html', error_messages=error_messages)

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return f'Bienvenue, {session["nom"]} !'
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

# Fermer la connexion MySQL à la fin du programme
mysql.close()
