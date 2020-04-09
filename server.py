import socketio
import eventlet
import eventlet.wsgi
import mysql.connector

sio = socketio.Server()
app = socketio.WSGIApp(sio)

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
        passwd='cs542'
    )
    print(mydb)
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app)
