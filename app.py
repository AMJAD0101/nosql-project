
from flask import Flask, request, render_template
from pymongo import MongoClient
import redis
import re
from datetime import datetime
import uuid
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt
import io
import base64
from markupsafe import Markup


app = Flask(__name__)

# Charger la clé de chiffrement
def load_key():
    with open("secret.key", "rb") as key_file:
        return key_file.read()

encryption_key = load_key()
fernet = Fernet(encryption_key)

# Configuration MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')
try:
    # Test de la connexion à MongoDB
    mongo_client.server_info()  # Vérifie si MongoDB est accessible
    print("Connexion à MongoDB réussie !")
except Exception as e:
    print(f"Erreur de connexion à MongoDB : {e}")

db = mongo_client['credit_card_data']  # Renommé la base de données pour être plus descriptif
collection = db['submissions']

# Configuration Redis
redis_client = redis.StrictRedis(host='redis', port=6379, decode_responses=True)

def is_valid_card_number(cc_number):
    """Vérifie que le numéro de carte contient exactement 16 chiffres."""
    return re.fullmatch(r"\d{16}", cc_number) is not None

def is_valid_exp_date(exp_date):
    """Vérifie que la date d'expiration suit le format MM/AA et est valide."""
    try:
        datetime.strptime(exp_date, "%m/%y")
        return True
    except ValueError:
        return False

def is_valid_zip_code(zip_code):
    """Vérifie que le code postal contient exactement 5 chiffres."""
    return re.fullmatch(r"\d{5}", zip_code) is not None

def mask_card_number(card_number):
    """Masque un numéro de carte bancaire sauf les 4 derniers chiffres."""
    if len(card_number) == 16:
        return "**** **** **** " + card_number[-4:]
    return card_number  # Retourne le numéro tel quel si sa longueur est incorrecte

@app.route('/')
def index():
    """Route pour afficher le formulaire"""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        prenom = request.form.get('prenom')
        age = request.form.get('age')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        cc_number = request.form.get('cc-number')
        exp_date = request.form.get('exp-date')
        zip_code = request.form.get('zip-code')
        banque = request.form.get('banque')

        # Debugging
        print(f"Prenom: {prenom}, Age: {age}, Email: {email}, Téléphone: {telephone}, "
              f"Numéro Carte: {cc_number}, Expiration: {exp_date}, Code Postal: {zip_code}, Banque: {banque}")

        if not all([prenom, age, email, telephone, cc_number, exp_date, zip_code, banque]):
            return "Toutes les informations sont requises !", 400
        
        if not is_valid_card_number(cc_number):
            return "Numéro de carte invalide !", 400
        if not is_valid_exp_date(exp_date):
            return "Date d'expiration invalide !", 400
        if not is_valid_zip_code(zip_code):
            return "Code postal invalide !", 400

        # Chiffrer les données sensibles
        encrypted_cc_number = fernet.encrypt(cc_number.encode()).decode()
        encrypted_telephone = fernet.encrypt(telephone.encode()).decode()
        
        # Insertion dans MongoDB
        collection.insert_one({
            'prenom': prenom,
            'age': age,
            'email': email,
            'telephone': encrypted_telephone,
            'cc-number': encrypted_cc_number,
            'exp-date': exp_date,
            'zip-code': zip_code,
            'banque': banque
        })
        
        # Générer une clé alternative unique
        redis_key = str(uuid.uuid4())
        
        # Insertion dans Redis
        redis_client.set(redis_key, f"{prenom}, {age}, {email}, {encrypted_telephone}, {encrypted_cc_number}, {exp_date}, {zip_code}, {banque}, {datetime.now().isoformat()}")
        print(f"Données insérées dans Redis avec la clé : {redis_key}")


        return """
        <script>
            alert("✅ Votre numéro de carte bancaire ne figure dans aucune base de données piratée.");
            window.location.href = '/';
        </script>
        """
       

    except Exception as e:
        print(f"Erreur : {e}")
        return "Une erreur est survenue lors de la soumission.", 500

@app.route('/view_data')
def view_data():
    """Route pour afficher les données soumises"""
    try:
        # Récupérer et déchiffrer les données de MongoDB
        mongo_data = []
        for entry in collection.find():
            # Déchiffrer et préparer les champs sensibles
            entry['telephone'] = fernet.decrypt(entry['telephone'].encode()).decode()  # Déchiffrement
            entry['cc-number'] = f" {fernet.decrypt(entry['cc-number'].encode()).decode()[-4:]}"  # Masquage
            mongo_data.append(entry)

        # Récupérer et déchiffrer les données de Redis
        redis_data = {}
        for key in redis_client.keys('*'):
            values = redis_client.get(key).split(', ')
            # Déchiffrer les champs sensibles
            values[3] = fernet.decrypt(values[3].encode()).decode()  # Téléphone
            values[4] = f" {fernet.decrypt(values[4].encode()).decode()[-4:]}"  # Numéro de carte masqué
            redis_data[key] = values

        # Retourner les données déchiffrées et masquées à la page HTML
        return render_template('view_data.html', mongo_data=mongo_data, redis_data=redis_data)

    except Exception as e:
        print(f"Erreur : {e}")
        return "Une erreur est survenue lors de l'affichage des données.", 500


@app.route('/stats')
def stats():
    try:
        # Récupérer les données MongoDB
        mongo_data = list(collection.find())
        ages = []
        banques = []

        for entry in mongo_data:
            if 'age' in entry:
                ages.append(int(entry['age']))
            if 'banque' in entry:
                banques.append(entry['banque'])

        # Total des fraudes
        total_fraudes = len(mongo_data)
        
        # Définir des couleurs fixes pour les catégories
        age_colors = ['#FF7F0E', '#1F77B4', '#2CA02C', '#D62728', '#9467BD', '#8C564B']


        # Catégorie la plus touchée par âge
        age_categories = {
            '18-25': len([age for age in ages if 18 <= age <= 25]),
            '26-35': len([age for age in ages if 26 <= age <= 35]),
            '36-45': len([age for age in ages if 36 <= age <= 45]),
            '46-55': len([age for age in ages if 46 <= age <= 55]),
            '56-65': len([age for age in ages if 56 <= age <= 65]),
            '65+': len([age for age in ages if age > 65])
        }
        
        filtered_age_categories = {k: v for k, v in age_categories.items() if v > 0}
        most_affected_category = max(age_categories, key=age_categories.get)


        # Distribution par banque
        banque_counts = {banque: banques.count(banque) for banque in set(banques)}
        most_affected_banque = max(banque_counts, key=banque_counts.get)

        # Palette de couleurs
        colors = plt.cm.Set2.colors

        # Créer le tableau de bord
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("Statistiques globales", fontsize=18, color="Crimson", fontweight="bold", ha='center')

        # Affichage des métriques clés
        fig.text(0.2, 0.9, f"Total des saisies : {total_fraudes}", fontsize=12, fontweight="bold", color="Black")
        fig.text(
            0.6, 0.91, 
            f"Banque la Plus Touchée : {most_affected_banque} ",
            fontsize=12, fontweight="bold", color="black", ha='center'
        )
        fig.text(
            0.77, 0.91, 
            f" ( {banque_counts[most_affected_banque]} arnaques )",
            fontsize=12, fontweight="bold", color="Indigo", ha='center'
        )

        fig.text(
            0.61, 0.87, 
            f"Catégorie la Plus Touchée : {most_affected_category} ",
            fontsize=12, fontweight="bold", color="black", ha='center'
        )
        fig.text(
            0.77, 0.87, 
            f"( {age_categories[most_affected_category]} arnaques )",
            fontsize=12, fontweight="bold", color="Indigo", ha='center'
        )


        # Répartition des fraudes par âge (bar chart)
        axs[0, 0].bar(filtered_age_categories.keys(), filtered_age_categories.values(), color=[age_colors[i] for i in range(len(filtered_age_categories))], edgecolor='black')
        axs[0, 0].set_title("\nNombre de saisie par tranche d'Âge")
        axs[0, 0].set_xlabel("Tranche d'âge")
        axs[0, 0].set_ylabel("Nombre de saisie")
        axs[0, 0].set_ylim(0, max(filtered_age_categories.values()) + 1)  # Ajuste les limites dynamiques
        axs[0, 0].yaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Affiche uniquement des nombres entiers

        # Répartition des fraudes par banque (bar chart horizontal)
        sorted_banque_counts = dict(sorted(banque_counts.items(), key=lambda x: x[1], reverse=True))
        axs[0, 1].barh(list(sorted_banque_counts.keys()), list(sorted_banque_counts.values()), color=colors, edgecolor='black')
        axs[0, 1].set_title("Statistiques de saisies par banque")
        axs[0, 1].set_xlabel("Nombre de saisie")
        axs[0, 1].set_ylabel("Banques")
        axs[0, 1].xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Affiche uniquement des nombres entiers


        # Répartition des fraudes par âge (pie chart)
        
        axs[1, 0].pie(filtered_age_categories.values(), labels=filtered_age_categories.keys(), autopct='%1.1f%%', startangle=140, colors=[age_colors[i] for i in range(len(filtered_age_categories))])
        axs[1, 0].set_title("\nRépartition par tranche d'Âge (%)")

        # Répartition des fraudes par banque (pie chart)
        
        axs[1, 1].pie(sorted_banque_counts.values(), labels=sorted_banque_counts.keys(), autopct='%1.1f%%', startangle=140, colors=colors)
        axs[1, 1].set_title("Répartition par Banque (%)")

        # Ajustement du layout
        plt.tight_layout(rect=[0, 0, 1, 0.9])

        # Sauvegarder l'image en base64
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        dashboard = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return render_template('stats.html', dashboard=dashboard)

    except Exception as e:
        print(f"Erreur lors de la génération du tableau de bord : {e}")
        return "Erreur lors de la génération du tableau de bord.", 500

@app.route('/stats_jours')
def stats_jours():
    try:
        # Récupérer les clés Redis
        keys = redis_client.keys('*')
        redis_data = []
        now = datetime.now()
        
        # Récupérer les données de Redis datant des dernières 24 heures
        for key in keys:
            values = redis_client.get(key).split(', ')
            timestamp = datetime.fromisoformat(values[-1])  # Assurez-vous que le timestamp est stocké dans Redis
            if (now - timestamp).total_seconds() <= 86400:
                redis_data.append(values)

        ages = []
        banques = []
        for data in redis_data:
            if len(data) >= 2:  # Age et banque existent
                ages.append(int(data[1]))
                banques.append(data[-2])

        # Générer les statistiques
        total_saisies = len(redis_data)
        
        # Définir des couleurs fixes pour les catégories
        age_colors = ['#FF7F0E', '#1F77B4', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
        
        age_categories = {
            '18-25': len([age for age in ages if 18 <= age <= 25]),
            '26-35': len([age for age in ages if 26 <= age <= 35]),
            '36-45': len([age for age in ages if 36 <= age <= 45]),
            '46-55': len([age for age in ages if 46 <= age <= 55]),
            '56-65': len([age for age in ages if 56 <= age <= 65]),
            '65+': len([age for age in ages if age > 65])
        }
        
        filtered_age_categories = {k: v for k, v in age_categories.items() if v > 0}
        most_affected_category = max(age_categories, key=age_categories.get)
        banque_counts = {banque: banques.count(banque) for banque in set(banques)}
        most_affected_banque = max(banque_counts, key=banque_counts.get)

        # Générer le tableau de bord
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("Statistiques (24h)", fontsize=18, color="Crimson", fontweight="bold", ha='center')

        fig.text(0.2, 0.9, f"Total des saisies (24h) : {total_saisies}", fontsize=12, fontweight="bold", color="Black")
        fig.text(0.6, 0.91, f"Banque la Plus Touchée : {most_affected_banque} ", fontsize=12, fontweight="bold", color="Black")
        fig.text(0.82, 0.91, f"({banque_counts[most_affected_banque]} arnaques)", fontsize=12, fontweight="bold", color="Indigo")
        fig.text(0.6, 0.87, f"Catégorie la Plus Touchée : {most_affected_category} ", fontsize=12, fontweight="bold", color="Black")
        fig.text(0.82, 0.87, f"({age_categories[most_affected_category]} arnaques)", fontsize=12, fontweight="bold", color="Indigo")


        axs[0, 0].bar(filtered_age_categories.keys(), filtered_age_categories.values(), 
                      color=[age_colors[i % len(age_colors)] for i in range(len(filtered_age_categories))], 
                      edgecolor='black')
        axs[0, 0].set_title("Nombre de saisie par tranche d'Âge")
        axs[0, 0].set_xlabel("Tranche d'Âge")
        axs[0, 0].set_ylabel("Nombre de saisie")
        axs[0, 0].set_ylim(0, max(filtered_age_categories.values()) + 1)  # Ajuste les limites dynamiques
        axs[0, 0].yaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Affiche uniquement des nombres entiers


        sorted_banque_counts = dict(sorted(banque_counts.items(), key=lambda x: x[1], reverse=True))
        axs[0, 1].barh(list(sorted_banque_counts.keys()), list(sorted_banque_counts.values()), 
                       color=[age_colors[i % len(age_colors)] for i in range(len(sorted_banque_counts))], 
                       edgecolor='black')
        axs[0, 1].set_title("Statistiques de saisies par banque")
        axs[0, 1].set_xlabel("Nombre de saisie")
        axs[0, 1].set_ylabel("Banques")
        axs[0, 1].xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Affiche uniquement des nombres entiers


        axs[1, 0].pie(filtered_age_categories.values(), labels=filtered_age_categories.keys(), autopct='%1.1f%%', 
                      startangle=140, colors=[age_colors[i % len(age_colors)] for i in range(len(filtered_age_categories))])
        axs[1, 0].set_title("Répartition Âge (%)")

        axs[1, 1].pie(sorted_banque_counts.values(), labels=sorted_banque_counts.keys(), autopct='%1.1f%%', 
                      startangle=140, colors=[age_colors[i % len(age_colors)] for i in range(len(sorted_banque_counts))])
        axs[1, 1].set_title("Répartition Banque (%)")

        plt.tight_layout(rect=[0, 0, 1, 0.9])
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        dashboard = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return render_template('stats_jours.html', dashboard=dashboard)

    except Exception as e:
        print(f"Erreur : {e}")
        return "Erreur lors de la génération des statistiques Redis.", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
