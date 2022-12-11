from flask import Flask, render_template, flash, session, redirect, request
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
import yaml, os

app = Flask(__name__)
Bootstrap(app)
CKEditor(app)

db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blogs")
    if result_value > 0:
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('index.html', blogs=blogs)
    return render_template('index.html', blogs=None)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>')
def blogs(id):
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blogs WHERE blog_id={}".format(id))
    if result_value > 0:
        blog = cursor.fetchone()
        return render_template('blogs.html', blog=blog)
    return 'Blog not found'

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        user_details = request.form
        if user_details['password'] != user_details['confirmpassword']:
            flash('Passwords do not match! Try again', 'danger')
            return render_template('register.html')
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO `users`(`firts_name`, `last_name`, `user_name`, `password`, `email`) VALUES (%s,%s,%s,%s,%s)", 
        (user_details['firstname'], user_details['lastname'], user_details['username'], generate_password_hash(user_details['password']), user_details['email']))
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful! Please login', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user_details = request.form
        username = user_details['username']
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM users WHERE user_name=%s", ([username]))
        if result_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'], user_details['password']):
                session['login'] = True
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                flash('Welcome ' + session['first_name'] + '! You have been successfully logged in', 'success')
            else:
                cursor.close()
                flash('Password incorrect', 'danger')
                return render_template('login.html')
        else:
            cursor.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cursor.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog', methods=['GET','POST'])
def write_blog():
    if request.method=='POST':
        blog_post = request.form
        title = blog_post['title']
        body = blog_post['body']
        author = session['first_name'] + ' ' + session['last_name']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO `blogs`(`title`, `author`, `body`) VALUES (%s,%s,%s)", (title, author, body))
        mysql.connection.commit()
        cursor.close()
        flash('Your blog post is added', 'success')
        return redirect('/')
    return render_template('write-blog.html')

@app.route('/my-blogs')
def my_blogs():
    author = session['first_name'] + ' ' + session['last_name']
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blogs WHERE author=%s", [author])
    if result_value > 0:
        my_blogs = cursor.fetchall()
        return render_template('my-blogs.html', my_blogs=my_blogs)
    else:
        return render_template('my-blogs.html', my_blogs=None)

@app.route('/edit-blog/<int:id>', methods=['GET','POST'])
def edit_blog(id):
    if request.method=='POST':
        cursor = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cursor.execute("UPDATE blogs SET title = %s, body = %s WHERE blog_id=%s", (title, body, id))
        mysql.connection.commit()
        cursor.close()
        flash('Update succesfully', 'success')
        return redirect('/blogs/{}'.format(id))
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT title, body FROM blogs WHERE blog_id=%s", ([id]))
    if result_value > 0:
        blog = cursor.fetchone()
        return render_template('edit-blog.html', blog=blog)

@app.route('/delete-blog/<int:id>')
def delete_blog(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM blogs WHERE blog_id={}".format(id))
    mysql.connection.commit()
    flash("Your post delete", 'success')
    return redirect('/my-blogs')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logout!', 'info')
    return redirect('/')

if __name__=='__main__':
    app.run(debug=True)