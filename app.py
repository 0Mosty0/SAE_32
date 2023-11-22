import pymysql
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email_address import validate_email

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
        mysql.commit()

# Route pour la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Route pour la page d'inscription (GET)
@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

# Route pour la soumission du formulaire d'inscription (POST)
@app.route('/signup', methods=['POST'])
def process_signup():
    nom = request.form.get('nom')
    email = request.form.get('email')
    mot_de_passe = request.form.get('mot_de_passe')

    # Validation de l'e-mail
    email_valid = validate_email(email)

    if not email_valid:
        return render_template('signup.html', email_valid=False)

    # Hash du mot de passe avant de le stocker dans la base de données
    mot_de_passe_hash = generate_password_hash(mot_de_passe)

    # Stockage des informations dans la base de données MySQL
    query = 'INSERT INTO utilisateurs (nom, email, mot_de_passe) VALUES (%s, %s, %s)'
    data = (nom, email, mot_de_passe_hash)
    
    try:
        with mysql.cursor() as cursor:
            cursor.execute(query, data)
            mysql.commit()
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return "Erreur lors de l'inscription"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
