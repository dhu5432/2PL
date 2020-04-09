import socketio
import mysql.connector

sio = socketio.Client()


@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error():
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


@sio.event
def message(data):
    print('I received a message!')


@sio.on('my message')
def on_message(data):
    print('I received a message!')


if __name__ =='__main__' :
    mydb = mysql.connector.connect(
        host='104.154.65.18',
        user='root',
        passwd='cs542'
    )

    sio.connect('http://34.68.155.98:8001')
