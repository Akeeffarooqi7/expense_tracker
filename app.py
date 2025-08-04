import os, random, string, datetime
from flask import Flask, render_template, redirect, url_for, request, session, send_file, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from config import Config
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# ✅ Corrected Config usage here
app.config['MYSQL_HOST'] = Config.MYSQL_HOST
app.config['MYSQL_USER'] = Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = Config.MYSQL_DB

# ✅ Mail configuration
app.config.update(
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_USE_TLS=Config.MAIL_USE_TLS,
    MAIL_USE_SSL=Config.MAIL_USE_SSL
)

mail = Mail(app)
mysql = MySQL(app)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(email,password_hash) VALUES(%s,%s)", (email, password))
        mysql.connection.commit()
        cur.close()
        flash('Registered! Login now.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        pw = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id,password_hash FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        cur.close()
        if row and check_password_hash(row[1], pw):
            session['user_id'] = row[0]
            session['email'] = email
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

def send_otp(email):
    otp = ''.join(random.choices(string.digits, k=6))
    expires = datetime.now() + timedelta(minutes=10)
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM otp_verification WHERE email=%s", (email,))
    cur.execute("INSERT INTO otp_verification(email, otp, expires_at) VALUES(%s,%s,%s)",
                (email, otp, expires))
    mysql.connection.commit()
    cur.close()
    msg = Message("Your OTP", sender=Config.MAIL_USERNAME, recipients=[email])
    msg.body = f"Your OTP for password reset is: {otp}"
    mail.send(msg)

@app.route('/reset_request', methods=['GET','POST'])
def reset_request():
    if request.method=='POST':
        email = request.form['email']
        send_otp(email)
        flash('OTP sent to email')
        return redirect(url_for('otp_verify', email=email))
    return render_template('reset_request.html')

@app.route('/otp-verify/<email>', methods=['GET','POST'])
def otp_verify(email=None):
    if request.method == 'GET':
        return render_template('otp_verify.html')
    # POST:
    email = request.args.get('email') or request.form.get('email') or session.get('verified_email')
    otp_input = request.form.get('otp', '').strip()
    if not email or not otp_input:
        flash('Email and OTP are required.')
        return redirect(url_for('reset_request'))
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT otp, expires_at FROM otp_verification WHERE email=%s", (email,))
    row = cursor.fetchone()
    cursor.close()
    if row and row[0] == otp_input and datetime.datetime.now() < row[1]:
        session['verified_email'] = email
        return redirect(url_for('reset_password'))
    flash('Invalid or expired OTP.')
    return redirect(url_for('reset_request'))




@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT country, category, amount, description, date, id  FROM expenses WHERE user_id=%s", (session['user_id'],))
    expenses = cur.fetchall()
    cur.execute("SELECT SUM(amount) FROM expenses WHERE user_id=%s AND YEAR(date)=YEAR(CURDATE())", (session['user_id'],))
    total_year = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(amount) FROM expenses WHERE user_id=%s AND MONTH(date)=MONTH(CURDATE())", (session['user_id'],))
    total_month = cur.fetchone()[0] or 0
    cur.close()
    return render_template('dashboard.html', expenses=expenses, total_month=total_month, total_year=total_year)

@app.route('/add', methods=['GET','POST'])
@login_required
def add_expense():
    if request.method=='POST':
        data = (session['user_id'], request.form['country'], request.form['currency'], request.form['category'],
                request.form['amount'], request.form['description'], formatted_datetime)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO expenses(user_id,country,currency,category,amount,description,date) VALUES(%s,%s,%s,%s,%s,%s,%s)", data)
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Deleted')
    return redirect(url_for('dashboard'))

@app.route('/reset_password', methods=['GET','POST'])
def reset_password():
    if 'verified_email' not in session:
        return redirect(url_for('reset_request'))
    if request.method == 'POST':
        new_pw = generate_password_hash(request.form['new_password'])
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password_hash=%s WHERE email=%s", (new_pw, session['verified_email']))
        mysql.connection.commit()
        cur.close()
        session.pop('verified_email')
        flash('Password reset successful. Login now.')
        return redirect(url_for('login'))
    return render_template('otp_verify.html')


@app.route('/download')
@login_required
def download():
    cur = mysql.connection.cursor()
    cur.execute("SELECT country, currency, category, amount, description, date FROM expenses WHERE user_id=%s", (session['user_id'],))
    data = cur.fetchall()
    cur.close()

    from fpdf import FPDF
    import tempfile

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Expense Statement', 0, 1, 'C')

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    for row in data:
        line = f"Date: {row[5]} | Country: {row[0]} | Currency: {row[1]} | Category: {row[2]} | Amount: {row[3]} | Desc: {row[4]}"
        pdf.multi_cell(0, 10, line)
        pdf.ln(1)

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        pdf.output(temp_pdf.name)
        temp_pdf.seek(0)
        return send_file(temp_pdf.name, mimetype='application/pdf', as_attachment=True, download_name="statement.pdf")



if __name__=='__main__':
    app.run(debug=True) 