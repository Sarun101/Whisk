from flask import Flask, Blueprint, render_template, flash, redirect, url_for, request
from .models import User
from . import db # Make sure to import your db instance here

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # FIXED: Modern SQLAlchemy 2.0 query syntax to fetch a user by email
        statement = db.select(User).where(User.email == email)
        user = db.session.execute(statement).scalar_one_or_none()

        if user:
            # Next step: Add password checking here
            pass

    return render_template('login.html')

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    return render_template('signup.html')
