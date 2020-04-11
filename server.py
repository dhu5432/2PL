import socketio
import eventlet
import eventlet.wsgi
import threading
import mysql.connector
from flask import Flask
from enum import Enum
from collections import deque

sio = socketio.Server()
app = socketio.WSGIApp(sio)
lock_table_lock = threading.Lock()
connection_lock = threading.Lock()
lock_table = {}
for i in range(0,999):
    lock_table[i] = ['O', 'O', 'O', 'O'] 

sid_to_id = {}
sid_num = 0
queue_of_operations = deque()

class transaction:
    def __init__(self, sid, tid, data, index):
        self.sid = sid
        self.tid = tid
        self.sorted_lock_requests = data
        self.index = index


def my_event(sid, data):
    pass

def sort_transaction(data):
    data.sort(key = lambda x: x[0])
    return data


def lookup_lock(operation, data_item):
    if operation == 'R':
        for i in lock_table[data_item]:
            if i == 'W':
                return False
        return True
    elif operation == 'W':
        for i in lock_table[data_item]:
            if i != 'O':
                return False
        return True
    else:
        print("IMPOSSIBLE")


@sio.on('execute_sql')
def execute_sql(sid, data): 
    print("Executing transaction {} from site {} on all sites".format(data[2], sid))
    sio.emit('execute_sql', data[1])
    lock_table_lock.acquire()
    for i in data[0]:
        lock_table[int(i)][sid_to_id[sid]] = 'O'
    lock_table_lock.release()

    if len(queue_of_operations) > 0:
        lock_table_lock.acquire()
        able_to_execute = True
        transaction = queue_of_operations.popleft()
        for i in range (transaction.index, len(transaction.sorted_lock_requests)):
            current_operation = transaction.sorted_lock_requests[i]
            if not lookup_lock(current_operation[1], current_operation[0]):
                transaction.index = i
                queue_of_operations.appendleft(transaction)
                able_to_execute = False
                break
            else:
                lock_table[current_operation[0]][sid_to_id[transaction.sid]] = current_operation[1]
        
        lock_table_lock.release()
        if able_to_execute:
            sio.emit('transaction granted', transaction.tid, room=sid)
        


@sio.on('transaction request')
def transaction_request(sid, data):
    temp = []
    for i in range(1, len(data)):
        temp.append([int(data[i][1]), data[i][0]])

    sorted_lock_requests = sort_transaction(temp)
    lock_table_lock.acquire()
    index = 0
    for i in sorted_lock_requests:

        if not lookup_lock(i[1], i[0]):
            print("Transaction {} from site {} could not be executed immediately".format(data[0], sid))
            t1 = transaction(sid, data[0], sorted_lock_requests, index)
            queue_of_operations.append(t1)
            return
        else: 
            lock_table[i[0]][sid_to_id[sid]] = i[1]
        index += 1
    
    
    for i in sorted_lock_requests:
        lock_table[i[0]][sid_to_id[sid]] = i[1]

    sio.emit('transaction granted', data[0], room=sid)
    lock_table_lock.release()
    

@sio.event
def connect(sid, environ):
    global sid_num
    print('connect ', sid)
    connection_lock.acquire()
    sid_to_id[sid] = sid_num
    sid_num += 1
    connection_lock.release()

@sio.event
def disconnect(sid):
    print('disconnect ', sid)



if __name__=='__main__':
    sid_num = 0
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app)
