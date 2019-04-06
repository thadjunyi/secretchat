# Secret Chat is a Web Chat Application hosted on Heroku using Python Web Server, Flask, SocketIO, mLab (Cloud-Hosted MongoDB), HTML and JavaScript

1. cd C:\Users\Thad\Heroku
2. virtualenv env
3. env\Scripts\activate
4. pip install flask
5. pip install gunicorn
6. git init
7. Create "Profile" and type web: gunicorn -k eventlet chat:app or web: gunicorn deploy:app
8. git push heroku master (push everything to heroku)
9. pip freeze > requirements.txt
10. git add .
11. git commit -m "committed!"
12. heroku create
13. heroku open (open url of the app)
14. git push heroku master