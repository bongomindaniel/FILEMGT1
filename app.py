from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb.cursors import DictCursor
from functools import wraps
import os

from werkzeug import secure_filename

app = Flask(__name__)

#mySQL config
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] = 'danny'
app.config['MYSQL_PASSWORD'] ="danny123"
app.config['MYSQL_DB']='myflaskapp'

app.config['UPLOAD_FOLDER'] = '/home/danny/Desktop/uploads'
# app.config['MYSQL_CURSORCLASS'] = 'DictCusor'

# mysql = MySQL()
# mysql.init_app(app)

#init MYSQL
mysql = MySQL(app)



# index page
@app.route('/')
def index():
  return render_template ('index.html')

# document page
@app.route('/documents')
def documents():
  return render_template('documents.html')

@app.route('/profile')
def profile():
  return render_template('profile.html')

# articles
@app.route('/articles')
def articles():
    # create sursor
  cur = mysql.connection.cursor()

  # get article
  results = cur.execute(" SELECT * FROM articles ")

  articles = cur .fetchall()

  if results > 0:
    return render_template('articles.html' , articles = articles)

  else:
      msg = 'NO ARTICLES FOUND'
      return render_template('articles.html' , msg = msg , articles = articles)

      # close connection
  cur.close()    


# single articles
@app.route('/article/<string:id>/')
def article(id):
    # create sursor
    cur = mysql.connection.cursor(DictCursor)

    # get article
    results = cur.execute("SELECT * FROM articles  WHERE id = %s", [id])

    article = cur .fetchone()
    return render_template('article.html', article = article)





# recent_documents
@app.route('/recentdocs')
def recentdocs():
    return render_template('recentdocs.html')
    

    
# register form class
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min =1 ,max=50)])
    username = StringField('username',[validators.Length(min=4, max=25)])
    email =  StringField('email',[validators.Length(min =1 ,max=50)])
    password = PasswordField('password',[
          validators.DataRequired(),
          validators.EqualTo('confirm',message='password do not match')
          ])
    confirm = PasswordField('confirm password')

    
# user  Registration
@app.route('/register',methods=['GET','POST'])
def register():    
    form = RegisterForm(request.form)
    if request.method ==  'POST' and form.validate():
       name = form.name.data
       email = form.email.data
       username = form.username.data
       password = sha256_crypt.encrypt(str(form.password.data))


      #  creating the cursor
       cur = mysql.connection.cursor()

      # excecute query
       cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name,email,username,password))

      #  commit to db
       mysql.connection.commit()
      #  close connection
       cur.close()

       flash('you are now registered and you can login to the system','success')


       redirect(url_for('index')) 
    return render_template('register.html', form=form)  

#user login   
@app.route('/login',methods=['GET','POST'])
def login():
  if request.method == 'POST':
    #get form fileds
    username = request.form['username']
    password_candidate =request.form['password'] 

    #create cusor
    cur = mysql.connection.cursor(DictCursor)

    #get user by user name
    result = cur.execute("SELECT * FROM users WHERE username = %s",[username])

    if result > 0:
       data = cur.fetchone()
       password = data['password']

       #compare passwords
       if sha256_crypt.verify(password_candidate,password):
           session['logged_in'] = True
           session['username'] = username


           flash('you are logged in ','success')
           return redirect(url_for('index'))
       else:
           error ='invalid login'
           return render_template('login.html',error = error)
    else:
        error ='username not found'
        return render_template('login.html',error = error )

    cur.close()

  return render_template('login.html') 

  # check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if'logged_in' in session:
           return f(*args,**kwargs)
        else:
          flash('unauthorised please login first','danger')
          return redirect(url_for('login'))

    return wrap      

# logout
@app.route('/logout')
@is_logged_in
def logout():
  session.clear()
  flash('you are logged out of the system','success')
  return redirect(url_for('login'))



# dashboard
@app.route('/dashboard')
@is_logged_in       
def dashboard():

  # create sursor
  cur = mysql.connection.cursor()

  # get article
  cur.execute("SELECT * FROM articles")

  articles = cur.fetchall()

  if article > 0:
    return render_template('dashboard.html' , articles = articles)

  else:
      msg = 'NO ARTICLES FOUND'
      return render_template('dashboard.html' , msg = msg)

      # close connection
  cur.close()    


# article form class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min =1 ,max=200)])
    body = TextAreaField('Body',[validators.Length(min=4)])


#add article
@app.route('/add_article', methods = ['GET','POST'])
@is_logged_in
def add_article():
  form = ArticleForm(request.form)
  if request.method == 'POST' and form.validate():
      title = form.title.data
      body = form.body.data

      # create cursor
      cur = mysql.connection. cursor()

      # excecute
      cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title , body ,session['username']))  

      # commit
      mysql.connection.commit()

      # close
      cur.close()

      flash('Article Created', 'success')

      return redirect(url_for('dashboard'))

  return render_template('add_article.html', form = form)   

@app.route('/get_article/<int:id>')
def get_article(id):
  form = ArticleForm(request.form)
  cur = mysql.connection. cursor()

      # excecute
  cur.execute("SELECT title,body FROM articles WHERE id='{}'".format(id))  

  the_article = cur.fetchone()

  print(the_article[0])
  return render_template('edit_article.html', form = form, article = the_article)

  # Edit article
@app.route('/edit_article/<int:id>' , methods = [ 'GET' , 'POST' ])
@is_logged_in
def edit_article(id):

  # creaate cursor
  cur = mysql.connection.cursor()

  # get article by id
  cur.execute("SELECT * FROM articles WHERE id = %s",[id])

  article = cur.fetchone()

  # get form
  form = ArticleForm(request.form)

  # populate article form fieldgit f
  form.title.data = article['title']
  form.body.data = article['body']
  if request.method == 'POST' and form.validate():
      title = request.form['title']
      body = request.form['body']

    
      cur = mysql.connection. cursor()

      # excecute
      cur.execute(" UPDATE articles SET title = %s , body = %s WHERE id = %s  " ,( title , body , id ))  

      # commit
      mysql.connection.commit()

      # close
      cur.close()

      flash(' Article updated ' , ' success ')

      return redirect(url_for(' dashboard '))

  return render_template('edit_article.html', form = form)




  # delete article
  @app.route('/delete_article/<string :id>',methods = ['POST'])
  @is_logged_in
  def delete_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # excecute
    
    cur.execute("DELETE FROM articles WHERE id = %s",[id])

  # commit
    mysql.connection.commit()

   # close
    cur.close()


    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


@app.route('/uploads', methods=['GET', 'POST'])
def upload_doc():
  if request.method == 'POST':
    our_doc = request.files['file']
    name = secure_filename(our_doc.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'],name)
    our_doc.save(path)

    try:
      cur = mysql.connection.cursor()

      # excecute
      sql = "INSERT INTO documents(document) values('{}')".format(our_doc.read())
      cur.execute(sql)

    # commit
      mysql.connection.commit()

    # close
      cur.close()

      flash('Successfully saved the document to database', 'success')
    except Exception as e:
      raise(e)
      flash('Error', 'danger')


  return render_template('documents.html')
  




  


if __name__ == '__main__':
     app.secret_key = 'secret123'
     app.run(debug = True)  