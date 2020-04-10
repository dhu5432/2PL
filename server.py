import socketio
import subprocess
from subprocess import Popen
import eventlet
import eventlet.wsgi
import mysql.connector
from random import randint
import string
import random

sio = socketio.AsyncServer()
app = socketio.ASGIApp(sio)

def my_event(sid, data):
    pass

@sio.on('my custom event')
def another_event(sid, data):
    pass

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)



if __name__=='__main__':
    mydb = mysql.connector.connect(
        host='35.232.71.137',
        user='root',
        passwd='cs542',
        database='cs542'
    )
    
    mycursor = mydb.cursor()
    
    for line in open("initial_db.sql"):
        mycursor.execute(line)
        mydb.commit()

    mycursor.execute("select * from `bank`")
    mycursor.fetchall()
    rc = mycursor.rowcount
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app)
