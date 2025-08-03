import os, random, string, datetime
from flask import Flask, render_template, redirect, url_for, request, session, send_file, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from config import Config
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
    expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
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

@app.route('/otp-verify', methods=['GET','POST'])
def otp_verify():
    email = request.form.get('email', '').strip()
    otp_input = request.form.get('otp', '').strip()

    if not email or not otp_input:
        flash('Email and OTP are required.')
        return redirect(url_for('reset_request'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT otp FROM otp_verification WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()

        if result and result[0] == otp_input:
            session['verified_email'] = email
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('otp_verify'))
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('reset_request'))


@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT country, currency, category, amount, description, date, id FROM expenses WHERE user_id=%s ORDER BY date DESC", (session['user_id'],))
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
                request.form['amount'], request.form['description'], request.form['date'])
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

@app.route('/download')
@login_required
def download():
    cur = mysql.connection.cursor()
    cur.execute("SELECT country,currency,category,amount,description,date FROM expenses WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()
    cur.close()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Country','Currency','Category','Amount','Description','Date'])
    writer.writerows(rows)
    buf.seek(0)
    return send_file(io.BytesIO(buf.read().encode()), mimetype="text/csv", as_attachment=True, download_name="statement.csv")

if __name__=='__main__':
    app.run(debug=True)
