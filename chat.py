# Flask by default reference to html pages from templates folder
from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
import datetime
import bcrypt

# https://flask-socketio.readthedocs.io/en/latest/
# https://github.com/socketio/socket.io-client

# Instantiating Flask application
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configuring the database link
#app.config['MONGO_DBNAME'] = 'secretchat'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/secretchat'
app.config['MONGO_DBNAME'] = 'secretchat'
app.config['MONGO_URI'] = 'mongodb://root:root999@ds119171.mlab.com:19171/secretchat'

mongo = PyMongo(app)
socketio = SocketIO(app)

@app.route( '/' )
def index():
    return render_template('./index.html')

def messageReceived():
    print( 'message was received!!!' )
    
@socketio.on( 'my event' )
def handle_my_custom_event( json ):
    print( 'received my event: ' + str( json ) )
    socketio.emit( 'my response', json, callback=messageReceived )
    roomName = str(json)
    if 'User Connected' not in roomName:
        roomCollection = json['room_name'].lower()
        room = mongo.db[roomCollection]
        storeMessage = room.insert({'name' : json['user_name'], 'date' : json['date'], 'message' : json['message']})
    

# Only POST for login as it will just process the login as the default is in login page, no template needed
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        db = mongo.db
        users = db.users
        login_user = users.find_one({'_id' : request.form['loginusername'].lower()})
        if login_user:
            hashloginpass = bcrypt.generate_password_hash(request.form['loginpassword'].encode('utf-8'))
            decodepass = bcrypt.generate_password_hash(login_user['password']).decode('utf-8')
            if ((bcrypt.check_password_hash(login_user['password'], request.form['loginpassword'])) and (login_user['_id']==request.form['loginusername'].lower())):
                succeed = []
                session['username'] = request.form['loginusername']
                succeed.append(session['username'])
                succeed.append(request.form['roomname'].upper())
                roomName = succeed[1].lower()
                oldRoomList = login_user['room list']

                if oldRoomList is None:
                    newRoomList = []
                    newRoomList.append(roomName.lower())
                else:
                    oldRoomList.append(roomName.lower())
                    newRoomList = list(set(oldRoomList))

                users.update_one({'_id' : request.form['loginusername'].lower()}, {'$set' : {'last room' : roomName, 'room list' : newRoomList}})
                room = db.roomName.find_one({'room name' : roomName})
                if room is None:
                    db.roomName.insert_one({'room name' : roomName})
                    oldMembers = []
                else:
                    oldMembers = room['members']

                oldMembers.append(request.form['loginusername'].lower())
                members = list(set(oldMembers))
                db.roomName.update_one({'room name' : roomName}, {'$set' : {'members' : members}})

                room = mongo.db[roomName]
                count = room.find().count()
                if count > 100:
                    roomText =  room.find().skip(room.count()-100)
                    counter = 100
                else:
                    roomText = room.find()
                    counter = count

                succeed.append(counter)
                if roomText is not None:
                    for text in roomText:
                        succeed.append(text)

                return render_template("./chat.html", data=succeed)
        return render_template("./index.html", data="Invalid username/password combination!")
    return render_template('./index.html')    

# POST is for register, GET returns the registration template
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'_id' : request.form['regusername']})
        
        if existing_user is None:
            if (request.form['regpassword'] == request.form['regpassword2']):
                hashpass = bcrypt.generate_password_hash(request.form['regpassword'].encode('utf-8'))
                users.insert({'_id' : request.form['regusername'].lower(), 'password' : hashpass, 'password2' : request.form['regpassword'], 'room list' : None})
                session['username'] = request.form['regusername']
                return render_template('./index.html')
            return render_template("./register.html", data="Password Mismatched!")

        return render_template("./register.html", data="That username already exists!")
    
    return render_template('./register.html')

if __name__ == '__main__':
    app.secret_key = 'secretchat'
    # app.run(debug=True)
    app.config['SESSION_TYPE'] = 'filesystem'
    sess.init_app(app)
    socketio.run( app, debug = True)
