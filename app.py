from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
import mysql.connector
import html, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
bcrypt = Bcrypt(app)

conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor(dictionary=True)

@app.route("/")
def index():
    return redirect("/connexion")

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom = html.escape(request.form["nom"])
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]
        role = request.form.get("role", "patient")
        hashed_pw = bcrypt.generate_password_hash(mot_de_passe).decode('utf-8')
        cursor.execute("INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES (%s, %s, %s, %s)",
                       (nom, email, hashed_pw, role))
        conn.commit()
        return redirect("/connexion")
    return render_template("inscription.html")

@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]
        cursor.execute("SELECT * FROM utilisateurs WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user["mot_de_passe"], mot_de_passe):
            session["user_id"] = user["id"]
            session["nom"] = user["nom"]
            session["role"] = user["role"]
            return redirect("/accueil")
    return render_template("connexion.html")

@app.route("/accueil")
def accueil():
    if "user_id" not in session:
        return redirect("/connexion")
    role = session["role"]
    nom = session["nom"]
    if role == "admin":
        return render_template("admin_accueil.html", nom=nom)
    elif role == "agent":
        cursor.execute("SELECT * FROM utilisateurs WHERE role = 'patient'")
        patients = cursor.fetchall()
        return render_template("agent_accueil.html", nom=nom, patients=patients)
    else:
        return render_template("accueil.html", nom=nom)

@app.route("/dossier", methods=["GET", "POST"])
def dossier():
    if request.method == "POST":
        groupe_sanguin = request.form["groupe_sanguin"]
        antecedents = html.escape(request.form["antecedents"])
        allergies = html.escape(request.form["allergies"])
        pathologies = html.escape(request.form["pathologies"])
        cursor.execute("INSERT INTO dossiers_medicaux (utilisateur_id, groupe_sanguin, antecedents, allergies, pathologies) VALUES (%s, %s, %s, %s, %s)",
            (session["user_id"], groupe_sanguin, antecedents, allergies, pathologies))
        conn.commit()
        return redirect("/accueil")
    return render_template("dossier.html")

@app.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect("/connexion")

if __name__ == "__main__":
    app.run()