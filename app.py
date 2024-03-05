from flask import Flask, jsonify, request
from bson import ObjectId, json_util
from flask_pymongo import PyMongo
from flasgger import Swagger
from flasgger import swag_from
from flask import request

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/bibliotheque'
mongo = PyMongo(app)
swagger = Swagger(app)

#@app.route('/')
#def index():
#    return render_template('index.html')

@swag_from('swagger/livres.yml')             
@app.route('/livres', methods=['GET', 'POST'])
def livres():
    if request.method == 'GET':  
        livres = list(mongo.db.livres.find())
        return json_util.dumps(livres)
        
    elif request.method == 'POST':
        nouveau_livre = request.json
        if 'titre' in nouveau_livre and 'auteur' in nouveau_livre and 'annee' in nouveau_livre:
            result = mongo.db.livres.insert_one(nouveau_livre)
            return jsonify({"message": "Livre ajouté avec succès", "id": str(result.inserted_id)})
        else:
            return jsonify({"message": "Les champs obligatoires (titre, auteur, annee) doivent être fournis"}), 400

@swag_from('swagger/livre.yml')             
@app.route('/livres/<id>', methods=['GET', 'PUT', 'DELETE'])
def livre(id):
    book_id = ObjectId(id)
    if request.method == 'GET':
        if livre:
            return json_util.dumps(livre)
        else:
            return jsonify({"message": "Livre non trouvé"}), 404
    elif request.method == 'PUT':
        # MAJ détails d'un livre spécifique
        modifications = request.json
        mongo.db.livres.update_one({"_id": book_id}, {"$set": modifications})
        return jsonify({"message": f"Livre avec l'ID {id} mis à jour"})
    elif request.method == 'DELETE':
        mongo.db.livres.delete_one({"_id": book_id})
        return jsonify({"message": f"Livre avec l'ID {id} supprimé"})

@swag_from('swagger/utilisateurs.yml')             
@app.route('/utilisateurs', methods=['POST', 'GET'])
def utilisateurs():
    if request.method == 'POST':
        nouveau_utilisateur = request.json
        if 'nom' in nouveau_utilisateur and 'prenom' in nouveau_utilisateur and 'email' in nouveau_utilisateur :
            result = mongo.db.utilisateurs.insert_one(nouveau_utilisateur)
            return json_util.dumps({"message": "Utilisateur créé avec succès", "id": str(result.inserted_id)})
        else:
            return jsonify({"message": "Les champs obligatoires (nom, prenom) doivent être fournis"}), 400
    elif request.method == 'GET':
        utilisateurs = list(mongo.db.utilisateurs.find())
        return json_util.dumps(utilisateurs)

@swag_from('swagger/utilisateur.yml')             
@app.route('/utilisateurs/<id>', methods=['GET', 'PUT', 'DELETE'])
def utilisateur(id):
    user_id = ObjectId(id)
    if request.method == 'GET':
        utilisateur = mongo.db.utilisateurs.find_one({"_id": user_id})
        if utilisateur:  
            return json_util.dumps({"utilisateur": utilisateur})
        else:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
    elif request.method == 'PUT':
        modifications = request.json
        mongo.db.utilisateurs.update_one({"_id": user_id}, {"$set": modifications})
        return json_util.dumps({"message": f"Utilisateur avec l'ID {id} mis à jour"})
    elif request.method == 'DELETE':
        mongo.db.utilisateurs.delete_one({"_id": user_id})
        return json_util.dumps({"message": f"Utilisateur avec l'ID {id} supprimé"})


@app.route('/utilisateurs/<id_utilisateur>/livres/emprunt/<id_livre>', methods=['POST'])
def emprunter_livre(id_utilisateur, id_livre):

    utilisateur = mongo.db.utilisateurs.find_one({"_id": ObjectId(id_utilisateur)})
    livre = mongo.db.livres.find_one({"_id": ObjectId(id_livre)})

    if utilisateur and livre and not livre.get("emprunteur"):
        # Si il est pas déjà emprunté
        nom_livre = livre.get("titre", "")
        nom_utilisateur = utilisateur.get("nom", "")
        auteur_livre = livre.get("auteur", "")

        # Ajoutez le livre a la liste des empruns de l'user
        mongo.db.utilisateurs.update_one(
            {"_id": ObjectId(id_utilisateur)},
            {"$push": {"livres_empruntes": {"id_livre": ObjectId(id_livre), "titre": nom_livre, "auteur": auteur_livre}}} # opérateur pour push dans mongodb
        )

        # Mettez à jour la collection des livres
        mongo.db.livres.update_one(
            {"_id": ObjectId(id_livre)},
            {"$set": {"emprunteur": {"id_utilisateur": ObjectId(id_utilisateur), "nom": nom_utilisateur}}} # opérateur pour push dans mongodb
        )

        return jsonify({"message": f"Le livre {nom_livre} avec l'ID {id_livre} emprunté par {nom_utilisateur} avec l'ID {id_utilisateur}"})
    else:
        return jsonify({"message": "Impossible d'emprunter le livre"}), 400
    
@app.route('/livres/retour/<id_livre>', methods=['POST'])
def retourner_livre(id_livre):

    livre = mongo.db.livres.find_one({"_id": ObjectId(id_livre)})  

    if livre and livre.get("emprunteur"):
        id_utilisateur = livre["emprunteur"]["id_utilisateur"]
        utilisateur = mongo.db.utilisateurs.find_one({"_id": ObjectId(id_utilisateur)})
        nom_livre = livre.get("titre", "")
        nom_utilisateur = utilisateur.get("nom", "")


        # Maj user
        mongo.db.utilisateurs.update_one(
             {"_id": ObjectId(id_utilisateur)},
             {"$unset": {"livres_empruntes": ""}}
         )

        # Maj livres
        mongo.db.livres.update_one(
            {"_id": ObjectId(id_livre)},
            {"$unset": {"emprunteur": ""}}
        )

        return json_util.dumps({"message": f"Le livre {nom_livre} avec l'ID {id_livre} retourné par {nom_utilisateur} avec l'ID {id_utilisateur}"})
    else:
        return json_util.dumps({"message": "Impossible de retourner le livre"}), 400


if __name__ == "__main__":
    app.run(debug=True)
