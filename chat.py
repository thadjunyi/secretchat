# flask by default reference to html pages from templates folder
from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
import datetime
import bcrypt

# instantiating Flask application
app = Flask(__name__)
bcrypt = Bcrypt(app)

# configuring the database link with mLab Cloud-Hosted MongoDB 
app.config['MONGO_DBNAME'] = 'secretchat'
app.config['MONGO_URI'] = 'mongodb://root:root999@ds119171.mlab.com:19171/secretchat'
# Local MongoDB
# app.config['MONGO_DBNAME'] = 'secretchat'
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/secretchat'

# connects to MongoDB server and Flask-SocketIO
mongo = PyMongo(app)
socketio = SocketIO(app)

# default route
@app.route('/')
def index():
    return redirect(url_for('login'))

# to print acknowledged message
def messageReceived():
    print('message was received!!!')

# when a message is received from the client
@socketio.on('my event')
def handle_my_custom_event(json):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)
    # insert message into the database with the room name as the collection name
    roomName = str(json)
    if 'User Connected' not in roomName:
        roomCollection = json['room_name'].lower()
        room = mongo.db[roomCollection]
        storeMessage = room.insert({'name' : json['user_name'], 'date' : json['date'], 'message' : json['message']})

# url for login
@app.route('/login', methods=['POST', 'GET'])
def login():
    # if 'POST', the client tries to login into his account
    if request.method == 'POST':
        db = mongo.db
        users = db.users
        # find the account with the username keyed by the client from the database
        login_user = users.find_one({'_id' : request.form['loginusername'].lower()})
        # if an account is found
        if login_user:
            # compare the keyed hashed password with the account hashed password 
            hashloginpass = bcrypt.generate_password_hash(request.form['loginpassword'].encode('utf-8'))
            decodepass = bcrypt.generate_password_hash(login_user['password']).decode('utf-8')
            # if the password matched
            if ((bcrypt.check_password_hash(login_user['password'], request.form['loginpassword'])) and (login_user['_id']==request.form['loginusername'].lower())):
                roomName = request.form['roomname'].lower()
                # update the room list of the client account
                oldRoomList = login_user['room list']
                # if the client is a new user
                if oldRoomList is None:
                    newRoomList = []
                    newRoomList.append(roomName)
                # client is not a new user
                else:
                    oldRoomList.append(roomName)
                    newRoomList = list(set(oldRoomList))
                users.update_one({'_id' : request.form['loginusername'].lower()}, {'$set' : {'last room' : roomName, 'room list' : newRoomList}})

                # update the member list of the room
                room = db.roomName.find_one({'room name' : roomName})
                if room is None:
                    db.roomName.insert_one({'room name' : roomName})
                    oldMembers = []
                else:
                    oldMembers = room['members']
                oldMembers.append(request.form['loginusername'].lower())
                # ensures that the member list is unique
                members = list(set(oldMembers))
                db.roomName.update_one({'room name' : roomName}, {'$set' : {'members' : members}})

                # redirect to chat room upon successful login with 2 parameters namely client name and room name
                return redirect(url_for('chat', name=request.form['loginusername'], room=request.form['roomname'].upper()))
        # if the account can't be found or the username and password not match
        return render_template("./index.html", data="Invalid username/password combination!")
    # if 'GET', display the login form
    return render_template('./index.html')    

# url for register
@app.route('/register', methods=['POST', 'GET'])
def register():
    # if 'POST', the client tries to register an account
    if request.method == 'POST':
        users = mongo.db.users
        # to check for duplicate username in the database
        existing_user = users.find_one({'_id' : request.form['regusername']})
        # if no such username exist
        if existing_user is None:
            # to check if the password matched with the retyped password
            if (request.form['regpassword'] == request.form['regpassword2']):
                # hash the password
                hashpass = bcrypt.generate_password_hash(request.form['regpassword'].encode('utf-8'))
                # insert the account detail into the database
                users.insert({'_id' : request.form['regusername'].lower(), 'password' : hashpass, 'password2' : request.form['regpassword'], 'room list' : None})
                # redirect to login page upon successful register
                return redirect(url_for('login'))
            # if the password is not matched with the retyped password
            return render_template("./register.html", data="Password Mismatched!")
        # if the same username exist
        return render_template("./register.html", data="That username already exists!")
    # if 'GET', display the register form
    return render_template('./register.html')

# url for chat
@app.route( '/chat', methods=['POST', 'GET'])
def chat():
    # create a list of parameters to be passed to chat.html
    succeed = []
    # appending username and room name to list
    succeed.append(request.args.get('name'))
    succeed.append(request.args.get('room'))
    roomName = request.args.get('room').lower()
    # count the number of history messages
    room = mongo.db[roomName]
    count = room.find().count()
    # if number of messages exceed 100, limit to 100
    if count > 100:
        roomText =  room.find().skip(room.count()-100)
        counter = 100
    else:
        roomText = room.find()
        counter = count
    # appending the number of messages to list
    succeed.append(counter)
    # append each text messages to list
    if roomText is not None:
        for text in roomText:
            succeed.append(text)
    # display chat.html with the parameters passed
    return render_template('./chat.html', data=succeed)

if __name__ == '__main__':
    # secret key for the application
    app.secret_key = 'secretchat'
    # start up the web server with socketio
    socketio.run(app, debug=True)
