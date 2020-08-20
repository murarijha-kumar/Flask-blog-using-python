from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from _datetime import datetime
from flask_mail import Mail
import json
import os
import math
from werkzeug.utils import secure_filename

local_server=True
with open('config.json','r') as f:
    params=json.load(f)["params"]
app = Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(MAIL_SERVER='smtp.gmail.com',MAIL_PORT='465',MAIL_USE_SSL=True,MAIL_USERNAME=params['USERNAME'],MAIL_PASSWORD=params['PASSWORD'])
mail=Mail(app)

if(local_server):

    app.config['SQLALCHEMY_DATABASE_URI']=params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db=SQLAlchemy(app)
class Contacts(db.Model):
    srno=db.Column(db.Integer,primary_key=True,nullable=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(120),nullable=False)
    phone_num=db.Column(db.String(12),nullable=True)
    msg=db.Column(db.String(100),nullable=False)
    date=db.Column(db.String(20),nullable=False)
class Posts(db.Model):
    srno=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(120),nullable=False)
    slug=db.Column(db.String(120),nullable=False)
    tagline=db.Column(db.String(12),nullable=True)
    content=db.Column(db.String(100),nullable=False)
    date=db.Column(db.String(20),nullable=False)
    img_file = db.Column(db.String(100), nullable=False)
@app.route('/')
def home():
    flash("Welcome", "success")
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    #pagination logic
    page=request.args.get('page')

    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
         #First
    if(page==1):
         prev="#"
         next="/?page="+str(page+1)
    elif(page==last):
        #last
        prev="/?page="+str(page-1)

        next="#"
    else:
        prev = "/?page="+str(page - 1)

        next = "/?page="+str(page + 1)

        posts=Posts.query.filter_by().all()[0:params["no_of_posts"]]
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)
@app.route('/about')
def about():
    return render_template('about.html',params=params)
@app.route('/contact',methods=['Get','Post'])
def contacts():
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        phone_num=request.form.get('phone')
        msg=request.form.get('message')
        entry=Contacts(name=name,phone_num=phone_num,msg=msg,email=email,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from'+name,sender=email,recipients=[params['USERNAME']],body=msg+"\n"+phone_num+"\n"+email)

    return render_template('contact.html',params=params)
@app.route("/post/<string:post_slug>",methods=['Get'])
def post(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)
@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user']== params['admin-user']:
        posts = Posts.query.all()

        return render_template('dashboard.html',params=params,posts=posts)

    if request.method=='POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if username==params['admin-user'] and userpass==params['admin-pass']:
            session['user']=username
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)
    return render_template('login.html',params=params)
@app.route("/edit/<string:srno>",methods=['GET','POST'])
def edit(srno):
    if 'user' in session and session['user']== params['admin-user']:
        if request.method=='POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()
            if srno=='0':
                post=Posts(title=box_title,slug=slug,tagline=tagline,content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.slug = slug
                post.tagline = tagline
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+srno)
        post=Posts.query.filter_by(srno=srno).first()

        return render_template('edit.html',params=params,post=post,srno=srno)
@app.route('/uploader',methods=['GET','POST'])
def upload():
    if 'user' in session and session['user']== params['admin-user']:
        if(request.method=='POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded suucessfully"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:srno>",methods=['GET','POST'])
def delete(srno):
    if 'user' in session and session['user']== params['admin-user']:
        post=Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
        return  redirect('/dashboard')


app.run(debug=True)

