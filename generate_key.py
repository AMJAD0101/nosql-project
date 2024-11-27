from cryptography.fernet import Fernet

# Générer une clé
key = Fernet.generate_key()

# Sauvegarder la clé dans un fichier
with open("secret.key", "wb") as key_file:
    key_file.write(key)

print(f"Clé générée et sauvegardée dans 'secret.key': {key.decode()}")
