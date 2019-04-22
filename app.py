import tweepy
import json
import twitter_cred
import pygal                                                        

from datetime import datetime, date

from flask import Flask, render_template, flash, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract  

from flask_login import LoginManager, UserMixin, current_user, login_user,logout_user,login_required


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed

from flask_bcrypt import Bcrypt

from pygal.style import Style
 
from email.utils import parsedate_tz, mktime_tz




















auth = tweepy.OAuthHandler(twitter_cred.CONSUMER_KEY, twitter_cred.CONSUMER_SECRET)
auth.set_access_token(twitter_cred.ACCESS_TOKEN, twitter_cred.ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)
app = Flask(__name__)
 
host="https://tnrp.herokuapp.com/"
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
 
db = SQLAlchemy(app)


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view ='login'

  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


import datetime


class Tweet(db.Model):
    __tablename__ = 'filteredtweets'

    tweet_id = db.Column(db.Integer, primary_key=True)
    user_name= db.Column(db.String,nullable=False)
    pro_pic=db.Column(db.String)
    media= db.Column(db.String, default="noMedia")#uploaded media 
    inTextAUrl=db.Column(db.String, default="noUrl")
    tweetText = db.Column(db.String, nullable=False) 
    date_posted = db.Column(db.DateTime)

  
    def __init__(self,tweetId,userName,proPic, text, uploadMedia,url):
        self.tweet_id = tweetId
        self.user_name = userName
        self.pro_pic = proPic
        self.tweetText=text
        self.media=uploadMedia
        self.inTextAUrl = url
        
  

    @classmethod
    def delta_time(cls, tweet_posted):
        now = datetime.datetime.now()
        td = now - tweet_posted
        days = td.days
        hours = td.seconds//3600
        minutes = (td.seconds//60)%60
        if days > 0:
            return tweet_posted.strftime("%d %B, %Y")
        elif hours > 0:
            return str(hours) + 'h'
        elif minutes > 0:
            return str(minutes) + 'm'
        else:
            return 'few seconds ago'



class User(db.Model,UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
 
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default='user')
    image_file = db.Column(db.String(20), nullable=False, default='user.png')
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)


    def __init__(self, name, email, password, role):
        self.username = name
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return '<User {0}>'.format(self.name)
 
 
    def toDict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'role': self.role
        }




# forms 




class RegForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validateUsername(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise validationError('Username is already taken')

    def validatEmail(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise validationError('email is already taken')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')




class UpdateAccountForm(FlaskForm):
    fname = StringField('FirstName',validators=[Length(min=2, max=20)])
    lname = StringField('LastName',validators=[Length(min=2, max=20)])

    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')















# routes


 

custom_style = Style(
  background='transparent',
  plot_background='transparent',
  foreground='#ffff',
  foreground_strong='#fff',
  foreground_subtle='#fffa',
  opacity='.6',
  opacity_hover='.9',
  transition='400ms ease-in',
  value_colors = '#fff'
#   colors=('#E853A0', '#E8537A', '#E95355', '#E87653', '#E89B53'))
)



@app.before_first_request
def setup():

   db.create_all()
   db.session.commit()

   User.query.filter(User.username == "Admin").delete()
   Admin_pw = bcrypt.generate_password_hash("password").decode('utf-8')
   admin = User( "Admin","admin@tnrp.com",Admin_pw, "Admin")
   admin.id=1
   db.session.add(admin)
 
   db.session.commit()

   logout_user()


def tweetLoader(terms):
   for status in tweepy.Cursor(api.search,q=terms,count=1000,lang="en",include_entities="True").items():
               tweet = Tweet.query.filter_by(tweet_id = status.id).first()
               if tweet:
                  username = str(status.user.screen_name)
                  statid = str(status.id)
                  
                  print("tweet exists already")
               else:

                  Urls = status.entities.get('urls',[])
                  media = status.entities.get('media', [])  
                  newTweet=Tweet(status.id,status.user.screen_name,status.user.profile_image_url_https,status.text,"NoMedia","NoUrl")

                  if(len(Urls) > 0):
                     newTweet.inTextAUrl=str(Urls[0]['expanded_url'])
                  if(len(media) > 0):
                     newTweet.media= str(media[0]['media_url_https'])

                  
                  datestring = status.created_at
                  newTweet.date_posted=datestring
                  db.session.add(newTweet)
                  db.session.commit()


                  



@app.route("/")
@app.route("/home")
def home():

   if current_user.is_authenticated:
      tweetLoader("trinidad is not a real place -filter:retweets")
      tweetLoader("#TrinidadIsNotARealPlace -filter:retweets")
      TweetCharts()
      page = request.args.get('page',1,type=int)
      records = Tweet.query.order_by(Tweet.date_posted.desc()).paginate(page=page,per_page=6)
      return render_template("feed.html",Tweets=records)
   else:
      return render_template("app.html",host=host)




@app.route("/login", methods=['GET', 'POST'])
def login():
   if current_user.is_authenticated:
         return redirect(url_for('home'))
   else:
      form = LoginForm()
      if form.validate_on_submit():
         user = User.query.filter_by(email = form.email.data).first()
         if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect (next_page) if next_page else redirect(url_for('home'))
         else:     
            flash('Login Unsuccessful. Please check username and password', 'danger')
      return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
   if current_user.is_authenticated:
      return redirect(url_for('home'))
   else:
      form = RegForm()
      if form.validate_on_submit():
         hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
         u = User( form.username.data, form.email.data,hashed_pw, "user")
        
         db.session.add(u)
         db.session.commit()
 
         msgstr = 'Account created for '+form.username.data+'!'
        #print(u.username)
         flash(msgstr, 'success')
         return redirect(url_for('login'))
   return render_template('reg.html', title='Register', form=form)


@app.route("/logout")
def logout():
   logout_user()
   return redirect(url_for('home'))


@app.route("/analytics")
@login_required
def analytics():

   if current_user.role =="Admin":
      records = User.query.all()
      image_file = url_for('static', filename='propics/' + current_user.image_file)
      chartData= UserCharts()
      tweetchart=TweetCharts()
      return render_template('analytics.html', tweetData=tweetchart, chartdata=chartData, Users=records,title='analytics',image_file=image_file)
   else:
      return redirect(url_for('home'))

   
def UserCharts():
 
   users = [None,None,None,None,None,None,None,None,None,None,None,None]
   for x in range(12):
      num=User.query.filter(extract('month', User.date_joined)==x+1).count()
      users[x]=num   
   line_chart = pygal.Bar(show_minor_y_labels=False,show_legend=False,  style=custom_style)
   line_chart.x_labels = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec'

   line_chart.title = 'New Users 2019'
   line_chart.add('users joined',users)
   graphdata = line_chart.render_data_uri()
   return graphdata

def TweetCharts():
 
   tweets = [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None]
   for x in range(24):
      num=Tweet.query.filter(extract('hour', Tweet.date_posted)==x).count()
      tweets[x]=num
   radar_chart = pygal.Radar(show_legend=False, show_minor_y_labels=False, fill=True,  style=custom_style)
   radar_chart.title = 'Post Time'
   radar_chart.x_labels = range(0,24)
   radar_chart.render_data_uri()


   radar_chart.add('Tweet By Hour',tweets)
   graphdata = radar_chart.render_data_uri()
   return graphdata

 
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.firstname=form.fname.data
        current_user.lastname = form.lname.data

        current_user.username = form.username.data
        current_user.email = form.email.data

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.fname.data = current_user.firstname
        form.lname.data = current_user.lastname

        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='propics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


# @app.route('/api/persons/<id>', methods=['PUT'])
# def api_update_person(id):
#     data = None
#     if request.content_type  == 'application/x-www-form-urlencoded':
#         data = request.form
#     elif request.content_type == 'application/json':
#         data = request.json
#     return jsonify(updatePerson(data, id))

# @app.route('/api/persons/<id>', methods=['DELETE'])
# def api_delete_person(id):
#     return jsonify(deletePerson(id))
 
if __name__ == '__main__':
    app.run(debug=False)