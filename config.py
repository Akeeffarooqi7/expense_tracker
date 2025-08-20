import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://expense_tracker:A2NCbGVVQhEDReVi4eoAsSJ29xCRPJKP@dpg-d2j1bih5pdvs73cok3ug-a.singapore-postgres.render.com/expense_tracker_db_e5ja"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Mail config
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == 'True'
app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL") == 'True'
