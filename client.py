import socketio
import mysql.connector
import argparse

sio = socketio.Client()
map_of_transactions = {}
master_list_of_transactions = []
transaction_num = 0
@sio.event
def connect():
    print("Connection with central site established")


@sio.event
def connect_error():
    print("Connection to central site failed")


@sio.event
def disconnect():
    print("Disconnected from central site")

@sio.on('execute sql')
def execute_sql(data):

    mydb = mysql.connector.connect(
        host='104.154.65.18',
        user='root',
        passwd='cs542',
        database='cs542'
    )
    mycursor = mydb.cursor(buffered=True)
    for i in data:
        mycursor.execute(i)
        mydb.commit()
    mycursor.close()
    mydb.close()
    

@sio.on('transaction granted')
def transaction_granted(data):
    global transaction_num
    print("Locks for transaction {} granted".format(data))
    sql_statements = []
    data_items = []
    transaction = map_of_transactions[data]
    mydb = mysql.connector.connect(
        host='104.154.65.18',
        user='root',
        passwd='cs542',
        database='cs542'
    )
    mycursor = mydb.cursor(buffered=True)
    
    for index in range(1, (len(transaction))):
        data_items.append(transaction[index][1])
        if transaction[index][0] == 'R':
            mycursor.execute("SELECT {} FROM bank where AccountNumber = {}".format(transaction[index][2], transaction[index][1])) 
        else:
            sql_string = "UPDATE bank set {} = {} WHERE AccountNumber = {}".format(transaction[index][2], transaction[index][3], transaction[index][1])
            mycursor.execute(sql_string)
            mydb.commit()
            sql_statements.append(sql_string)
    mycursor.close()
    mydb.close()
    combined = []
    combined.append(data_items)
    combined.append(sql_statements)
    combined.append(data)
    print("Successfully executed transaction {}".format(data))
    sio.emit('execute_sql', combined)




if __name__ =='__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, default='input/input_1.txt', help= 'Include which text file to run')
    args = parser.parse_args()
    
    mydb = mysql.connector.connect(
        host='104.154.65.18',
        user='root',
        passwd='cs542',
        database='cs542'
    )
    mycursor = mydb.cursor()
    
    for line in open("initial_db.sql"):
        mycursor.execute(line)
        mydb.commit()

    mycursor.close()
    mydb.close()
    sio.connect('http://34.68.155.98:8001')
    

    need_locks_for = []
    transaction_id = 0
    for line in open(args.input_file):
        if line.split()[0] == 'BT':
            transaction_id += 1
            need_locks_for.append(transaction_id)

        elif line.split()[0] == 'R':
            data_item = line.split()[1]
            column = line.split()[2]
            temp = ["R", data_item, column]
            need_locks_for.append(temp)

        elif line.split()[0] == 'W':
            data_item = line.split()[1]
            column = line.split()[2]
            value = line.split()[3]
            temp = ["W", data_item, column, value]
            need_locks_for.append(temp)

        elif line.split()[0] == 'C':
           map_of_transactions[transaction_id] = need_locks_for
           master_list_of_transactions.append(need_locks_for)
           need_locks_for = []
   
    for i in range(0, len(master_list_of_transactions)):
        sio.emit('transaction request', master_list_of_transactions[i])
