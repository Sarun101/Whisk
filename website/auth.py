from flask import Flask,Blueprint,render_template,flash,redirect,url_for

auth = Blueprint('auth',__name__)

@auth.route('/')
def sign_up():
    return render_template('base.html')