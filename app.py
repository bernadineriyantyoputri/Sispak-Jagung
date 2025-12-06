import os, json, csv, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from fc_engine import forward_chain
from model_utils import predict_image_stub

APP_ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
RULES_PATH = os.path.join(DATA_DIR, "rules.json")
LOG_CSV = os.path.join(LOG_DIR, "diagnoses.csv")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "ganti_dgn_key_aman"

# --- User handling ---
def load_users():
    if not os.path.exists(USERS_PATH):
        with open(USERS_PATH, "w") as f:
            json.dump({"users": []}, f)
    with open(USERS_PATH, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- Rules handling ---
if not os.path.exists(RULES_PATH):
    with open(RULES_PATH, "w") as f:
        json.dump({"rules": [], "symptoms": {}}, f, indent=2)

def load_rules():
    with open(RULES_PATH, "r") as f:
        return json.load(f)

# --- Login required decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("Silakan login dulu.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")  # dashboard user setelah login

@app.route("/diagnose", methods=["GET","POST"])
@login_required
def index():
    data = load_rules()
    symptoms = data.get("symptoms", {})

    if request.method == "POST":
        inputs = {k: float(request.form.get(k,0)) for k in symptoms.keys()}

        # optional: image
        file = request.files.get("image")
        model_probs = {}
        if file and file.filename != "":
            try:
                from PIL import Image
                img = Image.open(file.stream).convert("RGB")
                model_probs = predict_image_stub(img)
                for k,p in model_probs.items():
                    inputs[f"pred_{k}"] = float(p)
            except Exception as e:
                flash("Error saat memproses gambar: " + str(e), "danger")

        results = forward_chain(data.get("rules", []), inputs)

        # log diagnosis
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell()==0:
                writer.writerow(["timestamp","username","symptoms","model_probs","results"])
            writer.writerow([datetime.datetime.utcnow().isoformat(), session["username"], 
                             json.dumps(inputs), json.dumps(model_probs), json.dumps(results)])

        return render_template("result.html", results=results, inputs=inputs, symptoms=symptoms, model_probs=model_probs)

    return render_template("index.html", symptoms=symptoms)

# --- Auth ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users().get("users",[])
        user = next((u for u in users if u["username"]==username and u["password"]==password), None)
        if user:
            session["username"] = username
            flash("Login berhasil.", "success")
            return redirect(url_for("dashboard"))  # redirect ke dashboard
        flash("Username atau password salah.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        if not username or not password:
            flash("Username dan password wajib diisi.", "warning")
            return redirect(url_for("register"))
        users_data = load_users()
        if any(u["username"]==username for u in users_data["users"]):
            flash("Username sudah ada.", "warning")
            return redirect(url_for("register"))
        users_data["users"].append({"username": username, "password": password})
        save_users(users_data)
        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    flash("Logout berhasil.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
