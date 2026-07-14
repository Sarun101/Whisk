from flask import Flask,Blueprint,render_template,flash,redirect,url_for,request

auth = Blueprint('auth',__name__)

@auth.route('/',methods = ['GET','POST'])
def login():
    
    if request.method == 'POST':
        role = request.form.get('role')
        print(role)
    return render_template('login.html')