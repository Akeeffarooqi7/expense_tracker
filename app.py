import os
import random
import string
from datetime import datetime, timedelta
from functools import wraps
import tempfile

from flask import (
    Flask, render_template_string, request, redirect, url_for,
    session, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
from fpdf import FPDF
from sqlalchemy import extract, func

# Load environment
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24)

# PostgreSQL config (SQLAlchemy + psycopg2)
POSTGRES_USER = os.getenv('POSTGRES_USER', 'expense_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'expense_tracker_db')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config.update(
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 587)),
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', 'True') == 'True',
    MAIL_USE_SSL=os.getenv('MAIL_USE_SSL', 'False') == 'True',
)

mail = Mail(app)

# SQLAlchemy + Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ---------- Models ----------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    expenses = db.relationship('Expense', backref='user', cascade='all, delete-orphan', lazy=True)

class OTPVerification(db.Model):
    __tablename__ = 'otp_verification'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    otp = db.Column(db.String(10))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    amount = db.Column(db.Numeric(12,2))
    category = db.Column(db.String(100))
    currency = db.Column(db.String(10))
    country = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Try create tables at startup (safe for dev)
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print("DB setup warning:", e)

# --- Helpers ---
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    try:
        msg = Message("ExpenseTracker OTP", sender=app.config.get('MAIL_USERNAME'), recipients=[email])
        msg.body = f"Your OTP for password reset is: {otp}\nIt expires in 10 minutes."
        mail.send(msg)
        return True
    except Exception as e:
        print("Mail sending failed:", e)
        return False

# --- Base HTML (unchanged structure but fixed CSS JS issues) ---
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Expense Tracker</title>
<!-- Font Awesome for icons -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
  :root{
    --bg:#0b0b0c; --card:#121213; --muted:#9aa0a6; --accent:#4a90e2; --success:#28a745; --danger:#e04545; --text:#eef2f3;
    --radius:12px;
  }
  html,body{height:100%;margin:0;font-family:Segoe UI,Roboto,Inter,Arial;background:linear-gradient(180deg,var(--bg),#070708);color:var(--text);}
  .wrap{max-width:980px;margin:18px auto;padding:16px;}
  .navbar{display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--card);border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,0.6);position:relative;}
  .brand{font-weight:700;font-size:1.2rem;display:flex;align-items:center;gap:8px}
  .brand i{color:var(--accent);font-size:1.3em;}
  .navlinks{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
  .navlinks a{color:var(--text);text-decoration:none;margin-left:12px;padding:6px 10px;border-radius:8px;display:flex;align-items:center;gap:6px;transition:background 0.2s;}
  .navlinks a:hover{background:rgba(74,144,226,0.12);}
  .menu-toggle{display:none;cursor:pointer;background:none;border:none;padding:8px;position:absolute;right:12px;top:12px;z-index:20;color:var(--accent);font-size:1.6em;}
  .container{margin-top:14px}
  .card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:16px;border-radius:var(--radius);box-shadow:0 8px 30px rgba(0,0,0,0.5);}
  label{display:block;color:var(--muted);margin-bottom:6px}
  input, select, textarea { width:100%; box-sizing:border-box; padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.04); background:#0f1011; color:var(--text); font-size:1rem; margin-bottom:12px; outline:none; }
  input:focus, select:focus, textarea:focus { box-shadow:0 8px 20px rgba(74,144,226,0.06); border-color:rgba(74,144,226,0.18) }
  .row{display:flex;gap:12px;flex-wrap:wrap}
  .col{flex:1;min-width:160px}
  .btn{display:inline-block;padding:10px 14px;border-radius:10px;border:none;cursor:pointer;font-weight:700;transition:background 0.2s,box-shadow 0.2s;box-shadow:0 2px 8px rgba(74,144,226,0.04);}
  .btn i{margin-right:4px;}
  .btn-primary{background:var(--accent);color:white}
  .btn-primary:hover{background:#357abd;}
  .btn-success{background:var(--success);color:white}
  .btn-success:hover{background:#218838;}
  .btn-danger{background:var(--danger);color:white}
  .btn-danger:hover{background:#b83232;}
  .muted{color:var(--muted)}
  .table{width:100%;border-collapse:collapse;margin-top:10px}
  .table th,.table td{padding:10px;border-bottom:1px solid rgba(255,255,255,0.03);text-align:left;font-size:0.95rem;white-space:nowrap}
  .table th i{margin-right:4px;}
  .action-btns{display:flex;gap:6px;}
  footer{margin-top:16px;padding:12px;text-align:center;color:var(--muted);font-size:0.9rem}
  .form-wrap{max-width:520px;margin:12px auto}
  .pw-wrap{position:relative;display:flex;align-items:center}
  .pw-toggle{position:absolute;right:18px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:14px;color:#ccc;user-select:none}
  .alert{padding:10px;border-radius:8px;margin-bottom:12px}
  .alert-info{background:#0b2a3a;color:#cdeaf8}
  .alert-success{background:rgba(40,167,69,0.08);color:var(--success)}
  .alert-danger{background:rgba(224,69,69,0.06);color:var(--danger)}
  .table-container{overflow:auto}
  @media (max-width:900px){
    .wrap{padding:12px}
    .brand{font-size:1.05rem}
  }
  @media (max-width:700px){
    .navbar{flex-direction:column;align-items:flex-start;gap:8px;}
    .navlinks{width:100%;justify-content:flex-end}
    .brand{margin-bottom:4px;}
    .menu-toggle{display:block;}
    .navlinks{display:none;flex-direction:column;gap:0;background:var(--card);position:absolute;top:56px;right:12px;min-width:160px;padding:10px 0;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,0.4);z-index:10;}
    .navlinks.show{display:flex;}
    .navlinks a{margin:0;padding:12px 18px;}
  }
  @media (max-width:520px){
    .row{flex-direction:column}
    .wrap{padding:8px}
    .form-wrap{padding:8px}
    .navlinks{width:100%;justify-content:flex-end}
    .table th,.table td{font-size:0.9rem}
    .navbar{padding:8px;}
    .brand{font-size:0.98rem;}
    .btn{padding:8px 10px;font-size:0.98em;}
  }
</style>
<script>
  function toggleInputPassword(id, el){
    var p = document.getElementById(id); if(!p) return;
    if(p.type === 'password'){ p.type='text'; el.innerText='HIDE'; } else { p.type='password'; el.innerText='SHOW'; }
  }
  function confirmDelete(){ return confirm('Delete this expense?'); }
  function calculateTotal(){
    var amount = parseFloat(document.querySelector("input[name='amount']").value || 0);
    var qty = parseFloat(prompt('Enter quantity:') || 0);
    if(!isNaN(amount) && !isNaN(qty)){ alert('Total = ' + (amount*qty).toFixed(2)); } else { alert('Enter valid numbers'); }
  }
  // Hamburger menu toggle
  function toggleMenu(){
    var nav = document.getElementById('navlinks');
    if(nav){ nav.classList.toggle('show'); }
  }
</script>
</head>
<body>
  <div class="wrap">
    <nav class="navbar">
      <div class="brand"><i class="fa-solid fa-wallet"></i><a href="{{ url_for('dashboard') }}" style="color:inherit;text-decoration:none">ExpenseTracker</a></div>
      <button class="menu-toggle" onclick="toggleMenu()" aria-label="Menu"><i class="fa-solid fa-bars"></i></button>
      <div class="navlinks" id="navlinks">
        {% if session.user_id %}
          <span class="muted" style="margin-right:8px"><i class="fa-solid fa-user"></i> Hi {{ session.email }}</span>
          <a href="{{ url_for('dashboard') }}"><i class="fa-solid fa-chart-line"></i>Dashboard</a>
          <a href="{{ url_for('add_expense') }}"><i class="fa-solid fa-plus"></i>Add</a>
          <a href="{{ url_for('download') }}"><i class="fa-solid fa-file-arrow-down"></i>Download</a>
          <a href="{{ url_for('logout') }}"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
        {% else %}
          <a href="{{ url_for('login') }}"><i class="fa-solid fa-right-to-bracket"></i>Login</a>
          <a href="{{ url_for('register') }}"><i class="fa-solid fa-user-plus"></i>Register</a>
        {% endif %}
      </div>
    </nav>

    <div class="container">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, msg in messages %}
            <div class="alert {% if category=='success' %}alert-success{% elif category=='danger' %}alert-danger{% else %}alert-info{% endif %}">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}

      {{ content|safe }}
    </div>

    <footer>BUILT BY MOHAMMED AKEEF FAROOQI</footer>
  </div>
</body>
</html>
"""
#  • <a href="mailto:mf.akeef@gmail.com" style="color:inherit">mf.akeef@gmail.com</a>
# --- Routes ---

@app.route('/')
def index():
    return redirect(url_for('dashboard') if session.get('user_id') else url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        if not email or not password:
            flash('Email and password required', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('This email may already be registered', 'danger')
            return redirect(url_for('register'))
        pw_hash = generate_password_hash(password)
        try:
            user = User(email=email, password_hash=pw_hash)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully — login now', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print("Register error:", e)
            flash('Server error during registration', 'danger')
            return redirect(url_for('register'))

    content = """
    <div class="card form-wrap">
      <h2>Register</h2>
      <form method="POST" autocomplete="off">
        <label>Email</label>
        <input type="email" name="email" required placeholder="you@example.com">
        <label>Password</label>
        <div class="pw-wrap">
          <input id="reg_pw" type="password" name="password" required placeholder="At least 6 characters">
          <span class="pw-toggle" onclick="toggleInputPassword('reg_pw', this)">SHOW</span>
        </div>
        <button class="btn btn-primary" type="submit">Register</button>
        <p class="muted small">Already registered? <a href="{{ url_for('login') }}">Login</a></p>
      </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        if not email or not password:
            flash('Provide email and password', 'danger')
            return redirect(url_for('login'))
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            session['email'] = user.email
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    content = """
    <div class="card form-wrap">
      <h2>Login</h2>
      <form method="POST" autocomplete="off">
        <label>Email</label>
        <input type="email" name="email" required placeholder="you@example.com">
        <label>Password</label>
        <div class="pw-wrap">
          <input id="login_pw" type="password" name="password" required placeholder="Password">
          <span class="pw-toggle" onclick="toggleInputPassword('login_pw', this)">SHOW</span>
        </div>
        <button class="btn btn-primary" type="submit">Login</button>
        <p class="muted small"><a href="{{ url_for('reset_request') }}">Forgot password?</a></p>
        <p class="muted small">New? <a href="{{ url_for('register') }}">Register here</a></p>
      </form>
    </div>
    """
    rendered_content = render_template_string(content)
    return render_template_string(BASE_HTML, content=rendered_content)
 
# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))

# Reset request (send OTP)
@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            flash('Enter your registered email', 'danger')
            return redirect(url_for('reset_request'))
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)
        try:
            # remove old OTPs
            OTPVerification.query.filter_by(email=email).delete()
            db.session.commit()
            # add new
            new = OTPVerification(email=email, otp=otp, expires_at=expires_at)
            db.session.add(new)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("OTP DB error:", e)
            flash('Server error creating OTP', 'danger')
            return redirect(url_for('reset_request'))

        sent = send_otp_email(email, otp)
        if sent:
            flash('OTP sent to your email (expires in 10 minutes)', 'success')
        else:
            print("Generated OTP for", email, "->", otp)
            flash('Could not send email; OTP generated on server (check console).', 'info')

        return redirect(url_for('otp_verify', email=email))

    content = """
    <div class="card form-wrap">
      <h2>Reset Password</h2>
      <form method="POST">
        <label>Email</label>
        <input type="email" name="email" required placeholder="Registered email">
        <button class="btn btn-primary" type="submit">Send OTP</button>
      </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# OTP verify
@app.route('/otp-verify', methods=['GET', 'POST'])
@app.route('/otp-verify/<email>', methods=['GET', 'POST'])
def otp_verify(email=None):
    email = (email or request.args.get('email') or request.form.get('email') or '').strip().lower()
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        otp_input = (request.form.get('otp') or '').strip()
        if not email or not otp_input:
            flash('Email and OTP required', 'danger')
            return redirect(url_for('reset_request'))
        row = OTPVerification.query.filter_by(email=email).order_by(OTPVerification.id.desc()).first()
        if not row:
            flash('No OTP found for this email. Request a new one.', 'danger')
            return redirect(url_for('reset_request'))
        db_otp, expires_at = row.otp, row.expires_at
        if datetime.now() > expires_at:
            flash('OTP expired. Request a new one.', 'danger')
            return redirect(url_for('reset_request'))
        if otp_input != db_otp:
            flash('Incorrect OTP', 'danger')
            return redirect(url_for('otp_verify', email=email))
        session['verified_email'] = email
        flash('OTP verified — set your new password', 'success')
        return redirect(url_for('reset_password'))

    content = f"""
    <div class="card form-wrap">
      <h2>Verify OTP</h2>
      <form method="POST">
        <label>Email</label>
        <input type="email" name="email" required value="{email}">
        <label>OTP (6 digits)</label>
        <input type="text" name="otp" maxlength="6" required placeholder="123456">
        <button class="btn btn-primary" type="submit">Verify OTP</button>
      </form>
      <p class="muted small">Didn't get OTP? <a href="{{ url_for('reset_request') }}">Send again</a></p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# Set new password (after OTP)
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'verified_email' not in session:
        flash('You must verify OTP first', 'danger')
        return redirect(url_for('reset_request'))
    email = session['verified_email']
    if request.method == 'POST':
        new_pw = request.form.get('new_password') or ''
        if len(new_pw) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('reset_password'))
        hashed = generate_password_hash(new_pw)
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('register'))
            user.password_hash = hashed
            # cleanup OTPs
            OTPVerification.query.filter_by(email=email).delete()
            db.session.commit()
            session.pop('verified_email', None)
            flash('Password updated. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print("Reset password error:", e)
            flash('Failed to update password', 'danger')
            return redirect(url_for('reset_password'))
            

    content = """
    <div class="card form-wrap">
      <h2>Set New Password</h2>
      <form method="POST" autocomplete="off">
        <label>New Password</label>
        <div class="pw-wrap">
          <input id="new_pw" type="password" name="new_password" required placeholder="New password">
          <span class="pw-toggle" onclick="toggleInputPassword('new_pw', this)">SHOW</span>
        </div>
        <button class="btn btn-success" type="submit">Set Password</button>
      </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)
    

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        rows = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.date.desc(), Expense.id.desc()).all()
        today = datetime.now().date()
        total_year = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == session['user_id'],
            extract('year', Expense.date) == today.year
        ).scalar() or 0
        total_month = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == session['user_id'],
            extract('year', Expense.date) == today.year,
            extract('month', Expense.date) == today.month
        ).scalar() or 0
    except Exception as e:
        print("Dashboard DB error:", e)
        rows = []
        total_year = total_month = 0

    # Build rows HTML
    rows_html = ""
    for r in rows:
        try:
            amount_val = float(r.amount)
        except Exception:
            amount_val = 0.0
        rows_html += f"""
        <tr>
          <td>{r.date}</td>
          <td>{r.country or ''}</td>
          <td>{r.category or ''}</td>
          <td>{amount_val:.2f}</td>
          <td>{r.description or ''}</td>
          <td>
            <form method="POST" action="{ url_for('delete', id=r.id) }" onsubmit="return confirmDelete();">
              <button class="btn btn-danger" type="submit">Delete</button>
            </form>
          </td>
        </tr>
        """
    content = f"""
    <div class="card">
      <h2>Dashboard</h2>
      <div class="row" style="align-items:center;justify-content:space-between;margin-bottom:8px">
        <div class="col small">This Month: <strong>{float(total_month):.2f}</strong></div>
        <div class="col small">This Year: <strong>{float(total_year):.2f}</strong></div>
        <div style="min-width:200px;text-align:right">
          <a class="btn btn-primary" href="{ url_for('add_expense') }">Add Expense</a>
        </div>
      </div>
      <div class="table-container">
      <table class="table">
        <thead><tr><th>Date</th><th>Country</th><th>Category</th><th>Amount</th><th>Description</th><th>Action</th></tr></thead>
        <tbody>
          {rows_html if rows_html else '<tr><td colspan="6" class="muted">No expenses yet.</td></tr>'}
        </tbody>
      </table>
      </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# Add expense
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
      country = (request.form.get('country') or '').strip()
      currency = (request.form.get('currency') or '').strip()
      category = (request.form.get('category') or '').strip()
      amount = request.form.get('amount') or ''
      date = request.form.get('date') or ''
      description = request.form.get('description') or ''
      # Save last used country/currency in session
      session['last_country'] = country
      session['last_currency'] = currency
      # Save expense to DB
      try:
        exp = Expense(
          user_id=session['user_id'],
          country=country,
          currency=currency,
          category=category,
          amount=amount,
          date=date,
          description=description
        )
        db.session.add(exp)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('dashboard'))
      except Exception as e:
        db.session.rollback()
        print('Add expense error:', e)
        flash('Failed to add expense', 'danger')

    # Data for dropdowns
    countries = [
        ('India', 'INR', '₹', ''),
        ('United States', 'USD', '$', ''),
        ('United Kingdom', 'GBP', '£', ''),
        ('Canada', 'CAD', '$', ''),
        ('Australia', 'AUD', '$', ''),
        ('Germany', 'EUR', '€', ''),
        ('France', 'EUR', '€', ''),
        ('Japan', 'JPY', '¥', ''),
        ('China', 'CNY', '¥', ''),
        ('Singapore', 'SGD', '$', ''),
        # ... (add more as needed)
    ]
    # Add more countries as needed, or use your full list
    countries.sort(key=lambda x: x[0])
    categories = [
        'Food', 'Travel', 'Bills', 'Groceries', 'Shopping', 'Health', 'Education', 'Entertainment',
        'Rent', 'Utilities', 'Transport', 'Fuel', 'Insurance', 'Gifts', 'Charity', 'Investment',
        'Kids', 'Pets', 'Personal Care', 'Fitness', 'Phone', 'Internet', 'Subscriptions', 'Other'
    ]
    # Remember last used country/currency (from session)
    last_country = session.get('last_country', 'India')
    last_currency = session.get('last_currency', 'INR')
    today = datetime.now().date()
    # Build country options with data attributes for currency
    country_options = ''.join([
        f'<option value="{c[0]}" data-currency="{c[1]}" data-symbol="{c[2]}" data-flag="{c[3]}"' + (' selected' if c[0] == last_country else '') + f'>{c[3]} {c[0]}</option>'
        for c in countries
    ])
    category_options = ''.join([
        f'<option value="{cat}">{cat}</option>' for cat in categories
    ])
    # The currency field will be auto-filled and readonly
    content = f'''
    <div class="card">
      <h2>Add Expense</h2>
      <form method="POST">
        <div class="row">
          <div class="col">
            <label for="countrySelect">Country</label>
            <select name="country" id="countrySelect" required>
              <option value="" disabled>Select country</option>
              {country_options}
            </select>
          </div>
          <div class="col">
            <label for="currencyInput">Currency</label>
            <input type="text" name="currency" id="currencyInput" value="{last_currency}" readonly required>
          </div>
        </div>

        <label>Category</label>
        <select name="category" required>
          <option value="" disabled selected>Select category</option>
          {category_options}
        </select>

        <div class="row">
          <div class="col">
            <label>Amount</label>
            <input type="text" name="amount" placeholder="0.00" required>
          </div>
          <div class="col">
            <label>Date</label>
            <input type="date" name="date" value="{today}">
          </div>
        </div>

        <label>Description</label>
        <textarea name="description" placeholder="Optional note..."></textarea>

        <button class="btn btn-success" type="submit">Save</button>
        <button type="button" class="btn" onclick="calculateTotal()">Calculator</button>
      </form>
    </div>
    <script>
    // When country changes, update currency automatically
    document.getElementById("countrySelect").addEventListener("change", function() {{
      var selected = this.options[this.selectedIndex];
      var currency = selected.getAttribute('data-currency') || '';
      document.getElementById("currencyInput").value = currency;
    }});
    // On page load, set currency if a country is pre-selected
    window.addEventListener('DOMContentLoaded', function() {{
      var select = document.getElementById("countrySelect");
      var selected = select.options[select.selectedIndex];
      if(selected && selected.getAttribute('data-currency')) {{
        document.getElementById("currencyInput").value = selected.getAttribute('data-currency');
      }}
    }});
    </script>
    '''
    return render_template_string(BASE_HTML, content=content)

# Delete - POST only
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    try:
        Expense.query.filter_by(id=id, user_id=session['user_id']).delete()
        db.session.commit()
        flash('Deleted', 'success')
    except Exception as e:
        db.session.rollback()
        print("Delete error:", e)
        flash('Delete failed', 'danger')
    return redirect(url_for('dashboard'))

# Download PDF
@app.route('/download')
@login_required
def download():
    try:
        data = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.date.desc()).all()
    except Exception as e:
        print("Download query error:", e)
        data = []

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Expense Statement', 0, 1, 'C')
            self.ln(2)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)
    pdf.set_font('Arial', '', 11)


# Run
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
