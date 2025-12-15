import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

# ENGINE
from services.fc_engine import (
    forward_screening,
    forward_chain,
    get_confirmation_symptoms,
    predict_image_stub
)

# -------------------------------------------------------
# DIRECTORIES
# -------------------------------------------------------
APP_ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
RULES_PATH = os.path.join(DATA_DIR, "rules.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------------------------------------------
# RULES HANDLING
# -------------------------------------------------------
def load_rules():
    if not os.path.exists(RULES_PATH):
        with open(RULES_PATH, "w") as f:
            json.dump({"rules": [], "symptoms": {}}, f, indent=2)
    with open(RULES_PATH, "r") as f:
        return json.load(f)

def save_rules(data):
    with open(RULES_PATH, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------------------------------------
# Flask init
# -------------------------------------------------------
app = Flask(__name__)
app.secret_key = "ganti_dgn_key_aman"

# -------------------------------------------------------
# USERS HANDLING
# -------------------------------------------------------
def load_users():
    if not os.path.exists(USERS_PATH):
        with open(USERS_PATH, "w") as f:
            json.dump({"users": []}, f, indent=2)
    with open(USERS_PATH, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_PATH, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------------------------------------
# LOGIN REQUIRED DECORATOR
# -------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Silakan login dulu.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# -------------------------------------------------------
# DASHBOARD
# -------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

# =======================================================
# 1) SCREENING AWAL
# =======================================================
@app.route("/diagnose", methods=["GET", "POST"])
@login_required
def diagnose():
    data = load_rules()
    symptoms = data.get("symptoms", {})

    if request.method == "POST":
        # Ambil input screening awal
        inputs = {k: float(request.form.get(k, 0)) for k in symptoms.keys()}

        # OPTIONAL: prediksi gambar
        file = request.files.get("image")
        if file and file.filename != "":
            try:
                from PIL import Image
                img = Image.open(file.stream).convert("RGB")
                model_probs = predict_image_stub(img)
                for k, p in model_probs.items():
                    inputs[f"pred_{k}"] = float(p)
            except Exception as err:
                flash(f"Error gambar: {err}", "danger")

        # Screening kandidat penyakit
        candidates = forward_screening(data["rules"], inputs)
        if not candidates:
            flash("Tidak ada kandidat penyakit yang cocok.", "warning")
            return render_template("index.html", symptoms=symptoms)

        session["screen_inputs"] = inputs
        session["candidates"] = candidates

        return redirect(url_for("confirm"))

    return render_template("index.html", symptoms=symptoms)

# =======================================================
# 2) KONFIRMASI GEJALA TAMBAHAN
# =======================================================
@app.route("/confirm", methods=["GET", "POST"])
@login_required
def confirm():
    if "candidates" not in session:
        return redirect(url_for("diagnose"))

    data = load_rules()
    candidates = session["candidates"]
    symptoms_all = data["symptoms"]

    # Ambil gejala penting dari kandidat
    important_symptoms = get_confirmation_symptoms(
        candidates,
        symptoms_all,
        data["rules"]
    )

    # Nama penyakit kandidat
    candidate_names = [
        r["name"] for r in data["rules"]
        if r["id"] in candidates
    ]

    if request.method == "POST":
        # 🔥 FIX UTAMA DI SINI
        confirm_inputs = {
            k: float(request.form.get(k, 0))
            for k in important_symptoms.keys()
        }

        session["confirm_inputs"] = confirm_inputs
        return redirect(url_for("result_final"))

    return render_template(
        "confirm.html",
        candidate_names=candidate_names,
        important_symptoms=important_symptoms
    )

# =======================================================
# 3) HASIL AKHIR DIAGNOSA (1 PENYAKIT TERBAIK)
# =======================================================
@app.route("/result_final")
@login_required
def result_final():
    if "screen_inputs" not in session or "confirm_inputs" not in session:
        return redirect(url_for("diagnose"))

    data = load_rules()

    # Gabungkan input screening + konfirmasi
    merged_inputs = {}
    merged_inputs.update(session["screen_inputs"])
    merged_inputs.update(session["confirm_inputs"])

    # Hitung CF semua penyakit
    results_all = forward_chain(data["rules"], merged_inputs)

    # Ambil CF tertinggi
    best_result = results_all[0] if results_all else None

    return render_template(
        "result.html",
        best=best_result,
        results=results_all,
        symptoms=data["symptoms"],
        inputs=merged_inputs
    )

# =======================================================
# AUTH SYSTEM
# =======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users().get("users", [])
        user = next(
            (u for u in users if u["username"] == username and u["password"] == password),
            None
        )

        if user:
            session["username"] = username
            flash("Login berhasil.", "success")
            return redirect(url_for("dashboard"))

        flash("Username atau password salah.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username dan password wajib diisi.", "warning")
            return redirect(url_for("register"))

        users_data = load_users()
        if any(u["username"] == username for u in users_data["users"]):
            flash("Username sudah ada.", "warning")
            return redirect(url_for("register"))

        users_data["users"].append({
            "username": username,
            "password": password
        })
        save_users(users_data)

        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logout berhasil.", "success")
    return redirect(url_for("login")) 



# -------------------------------------------------------
# RUN APP
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
