import socketio
import time
import eventlet
import eventlet.wsgi
import threading
import mysql.connector
from collections import deque
from engineio.payload import Payload

blocked = 0
executed = 0
start = time.time()
end = time.time()

blocked_lock = threading.Lock()
executed_lock = threading.Lock()
sio = socketio.Server()
app = socketio.WSGIApp(sio)


lock_table_lock = threading.Lock()
connection_lock = threading.Lock()
lock_table = {}
for i in range(1,999):
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



def sort_transaction(data):
    data.sort(key = lambda x: x[0])
    return data


def lookup_lock(operation, data_item):
    if operation == 'R':
        lock_table_lock.acquire()
        for i in lock_table[data_item]:
            if i == 'W':
                lock_table_lock.release()
                return False

        lock_table_lock.release()
        return True
        lock_table_lock.release()
    elif operation == 'W':
        lock_table_lock.acquire()
        for i in lock_table[data_item]:
            if i != 'O':
                lock_table_lock.release()
                return False
        lock_table_lock.release()
        return True
    else:
        print("IMPOSSIBLE")


@sio.on('execute')
def execute_sql(sid, data): 
    global queue_of_operations
    global blocked
    global executed
    global end

    print("Executing transaction {} from site {} on all sites".format(data[2], sid_to_id[sid]))
    sio.emit('execute_sql', data[1], skip_sid=sid)
    lock_table_lock.acquire()
    for i in data[0]:
        lock_table[int(i)][sid_to_id[sid]] = 'O'
    lock_table_lock.release()
    print("Released locks used in transaction {} from site {}".format(data[2], sid_to_id[sid]))
   
    if len(queue_of_operations) > 0:
            temp_queue = deque()
            while(len(queue_of_operations)>0):
                able_to_execute = True
                transaction = queue_of_operations.popleft()
                for i in range(transaction.index+1, len(transaction.sorted_lock_requests)):
                    current_operation = transaction.sorted_lock_requests[i]
                
                    if not lookup_lock(current_operation[1], current_operation[0]):
                        transaction.index = i
                        temp_queue.append(transaction)
                        #queue_of_operations.appendleft(transaction)
                        able_to_execute = False
                        continue
                    else:    
                        lock_table_lock.acquire()
                        lock_table[current_operation[0]][sid_to_id[transaction.sid]] = current_operation[1]
                        lock_table_lock.release()
                if able_to_execute:
                    executed_lock.acquire()
                    executed+=1
                    if executed == 12000:
                        end = time.time()
                    executed_lock.release()
                    sio.emit('transaction granted', transaction.tid, room=transaction.sid)
            queue_of_operations = temp_queue
        


@sio.on('transaction request')
def transaction_request(sid, data):
    global queue_of_operations
    global blocked
    global executed
    global start
    global end
    temp = []
    print("{} is requesting a transaction".format(sid_to_id[sid]))
    for i in range(1, len(data)):
        temp.append([int(data[i][1]), data[i][0]])

    sorted_lock_requests = sort_transaction(temp)
    index = 0
    for i in sorted_lock_requests:

        if not lookup_lock(i[1], i[0]):
            #print("Transaction {} from site {} could not be executed immediately".format(data[0], sid_to_id[sid]))
            if(i[1] =='R'):
                print("Transaction {} from site {} is a Read operation  on row {}, but another transaction is currently writing to it".format(data[0], sid_to_id[sid], i[0]))
            else:
                print("Transaction {} from site {} is a Write operation  on row {}, but another transaction is currently reading or writing to it".format(data[0], sid_to_id[sid], i[0]))

            blocked_lock.acquire()
            blocked += 1
            blocked_lock.release()
            t1 = transaction(sid, data[0], sorted_lock_requests, index)
            queue_of_operations.append(t1)
            return
        else: 
            lock_table_lock.acquire()
            lock_table[i[0]][sid_to_id[sid]] = i[1]
            lock_table_lock.release()

        index += 1
    
    lock_table_lock.acquire()
    for i in sorted_lock_requests:
        lock_table[i[0]][sid_to_id[sid]] = i[1]
    lock_table_lock.release()
    executed_lock.acquire()
    if executed == 0:
        start = time.time()
    executed+=1
    if executed == 12000:
        end = time.time()

    executed_lock.release()
    sio.emit('transaction granted', data[0], room=sid)
    

@sio.event
def connect(sid, environ):
    global sid_num
    print("Site {} connected".format(sid_num))
    connection_lock.acquire()
    sid_to_id[sid] = sid_num
    sid_num += 1
    connection_lock.release()

@sio.event
def disconnect(sid):
    global blocked
    global executed
    print("{} transactions blocked in total".format(blocked))
    print("{} transactions executed in total".format(executed))
    print("{} took to execute all {} transactions".format(end-start, executed))
    print("Site {} disconnected".format(sid_to_id[sid]))

def empty_deque():
    while True:
        if len(queue_of_operations) > 0:
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
                    lock_table_lock.acquire()
                    lock_table[current_operation[0]][sid_to_id[transaction.sid]] = current_operation[1]
                    lock_table_lock.release()
            if able_to_execute:
                sio.emit('transaction granted', transaction.tid, room=transaction.sid)
        else:
            time.sleep(2)
     

if __name__=='__main__':
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app, log_output=False)
