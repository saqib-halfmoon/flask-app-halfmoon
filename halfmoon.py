#--------------------------------
#!/usr/bin/env python
# Copyright 2013 Halfmoon Labs, Inc.
# All Rights Reserved
#--------------------------------

import os
import sqlite3
import hashlib, random
from flask import Flask, render_template, send_from_directory, request, session, g, redirect, url_for, \
abort, render_template, flash
from time import gmtime, strftime
from contextlib import closing
from forms import RegistrationForm


#----------------------------------------
# initialization
#----------------------------------------

app = Flask(__name__)

#----------------------------------------
# configuration
#----------------------------------------

#app.config.from_envvar('Halfmoon_SETTINGS', silent=True)

app.config.update(   
    DEBUG = True,
    DATABASE = 'app.db',
    SECRET_KEY = 'unbreakablersapublickey',
    USERNAME = 'admin',
    PASSWORD = 'default',
)

#----------------------------------------
# controllers                   
#----------------------------------------
 
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
    	with app.open_resource('schema.sql', mode='r') as f:
    		db.cursor().executescript(f.read())
    	db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close() 

@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)  

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',[request.form['title'], request.form['text']])
    g.db.commit()   
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries')) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
    else:
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))                        


@app.route("/user/<username>/")
def user(username):
    message = 'Welcome %s!' % username
    return render_template('user.html', message=message) 

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/time")
def index():
	time_now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
	return render_template('index.html', time_now=time_now)

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)    

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha224(str(random.getrandbits(256))).hexdigest()
    return session['_csrf_token']


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        flash('Thanks for registering')
        return redirect(url_for('show_entries'))
    return render_template('register.html', form=form)    

    
#----------------------------------------
# launch
#----------------------------------------

app.jinja_env.globals['csrf_token'] = generate_csrf_token

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)