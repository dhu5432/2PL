### Infrastructure

The entire project runs on the [Google Cloud Platform](https://cloud.google.com/) using VMs and CloudSQL instances. To request access to the
project (and the VMs and databases associated with the system), please give me a gmail to add. 

### Description of Files

```servercopy.py``` This is the centralized transaction/lock manager that holds the lock table. 

```client.py``` This is a data site that is connected to a MySQL database. Within the Google Cloud Platform, I have 4 separate VMs that have a ```client.py``` script, but with lines ```27``` and ```89``` changed because each VM/data site is connected to its own MySQL database. 

```initial_db.sql``` When every data site begins running, it runs this file in order to make sure all databases on all data sites are in a consistent state with each other. 

### Walkthrough of Algorithm*

The algorithm starts at a data site sending a [transaction request](https://github.com/dhu5432/2PL/blob/master/client.py#L132) message with locally identifiable transaction ID, with a list of data rows and their operations for that specific transaction. So a transaction request with the payload 

```[34, [R, 100, Balance, [W, 308, Assets, 100]]```

means that this is transaction 34 from that data site, and the transaction wants to read row 100's balance and change row 308's Assets to 100. 

The lock manager [receives the transaction request](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L113) and processes it as it sees fit. If the transaction is granted, it replies back to the data site with a [transaction granted](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L161) message. 

Once the data site [receives](https://github.com/dhu5432/2PL/blob/master/client.py#L41) the transaction granted message, it executesthe corresponding queries and responds back with an [execute](https://github.com/dhu5432/2PL/blob/master/client.py#L78) message. 

Once the lock manager [receives](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L69) the execute message. It broadcasts to the other 3 data sites the SQL queries to be executed and releases all locks associated with the current transaction request. 


*A much more detailed walkthrough of my implementation's algorithm is given in the project report, but this is to help associate the code written with each step of the algorithm.

### Output
My report mentions that "I add a multitude of ```print``` statements throughout my implementation in order to understand what the system is doing at any given time". I detail the kind of output my system gives in this section. 

#### Lock Manager Output
```i is requesting a transaction``` When some data site ```i``` sends a transaction request message to the lock manager, the lock manager outputs to the console in order to acknowledge the receipt of the transaction request. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L121)

```Transaction j from site i is a Read operation on row k, but another transaction is currently writing to it``` When data site ```i``` sends transaction ```j``` to the lock manager, the lock manager looks in the lock table and outputs if it is currently unable to grant the transaction because another transaction has a write lock on one of the rows transaction ```j``` needs a read lock for. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L132)

```Transaction j from site i is a Write operation on row k, but another transaction is currently reading or writing ot it``` When data site ```i``` sends transaction ```j``` to the lock manager, the lock manager looks in the lock table and outputs if it is currently unable to grant the transaction because another transaction is currently reading or writing to row ```j```. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L134)

```Executing transaction j from site i on all sites``` When data site ```i``` has successfully executed transaction ```j```, it sends the lock manager the SQL queries that need to be executed at all other data sites. This outputs right before the lock manager broadcasts the SQL queries to execute on the other data sites. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L134)

```Released locks used in transaction j from site i``` After the lock manager broadcasts to all data sites the SQL queries to be executed for transaction j, it releases the locks associated with transaction j and this outputs. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L82)

#### Data Site Output
```Locks for transaction i granted``` As mentioned in the report, at each data site, each transaction is given an ID. A transaction ID and a data site ID can globally identify all transactions. This output means that transaction ```i``` can now be executed on the site that outputs this statement. [In the code](https://github.com/dhu5432/2PL/blob/master/client.py#L44)

```Successfully executed transaction i``` After the locks for transaction ```i``` have been granted, it connects to the MySQL database and executes all corresponding SQL queries. Once it finishes, this statement outputs. [In the code](https://github.com/dhu5432/2PL/blob/master/client.py#L77)

#### Test Cases to run during demo

* All 4 data sites running the transactions in [all_same_read.txt](https://github.com/dhu5432/2PL/blob/master/input/all_same_read.txt). I show that even though all of these transaction only read a single row, since read locks are compatible with each other, they transactions are executed immediately upon receipt by the lock manager with no blocking. 

* All 4 data sites running the transactions in [all_same_write.txt](https://github.com/dhu5432/2PL/blob/master/input/all_same_write.txt). I show that since all of these transactions are writing to a single row, and write locks are incompatible with each other, almost all the transaction requests are blocked by the lock manager to be executed later. 

* All 4 data sites running the transaction in mix\*_large.txt (site 1 will run [mix1_large.txt](https://github.com/dhu5432/2PL/blob/master/input/mix1_large.txt), site 2 will run [mix2_large.txt](https://github.com/dhu5432/2PL/blob/master/input/mix2_large.txt), etc.). Each of the data sites will be runnin 1000 transactions which means the lock manager will process a total of 4000 transactions. There are relatively few conflicts between these transactions since the queries can access any row within the database and the output will show that accordingly.


* All 4 data sites running the transaction in mix\*_many_conflicts.txt (site 1 will run [mix1_many_conflicts.txt](https://github.com/dhu5432/2PL/blob/master/input/mix1_many_conflicts.txt), site 2 will run [mix2_many_conflicts.txt](https://github.com/dhu5432/2PL/blob/master/input/mix2_many_conflicts.txt), etc.). Each of the data sites will be runnin 1000 transactions which means the lock manager will process a total of 4000 transactions. There are many conflicts between these transactions since the queries can only access between rows 100-110 and the output will show that accordingly. 

#### How to run

##### On Google Cloud
* ```ssh``` into all 5 VMs from the Google Cloud Console
* On the VM labeled ```central-site```:
    * ```cd 2PL```
    * Run ```python3 servercopy.py``` 
* On the VMs labeled ```site1, site2, site3, and site4```
    * ```cd 2PL```
    * Run ```python3 client.py ---input_file=input/all_same_write.txt``` where ```input/all_same_write.txt``` is the list of queries to submit to the data site
* Make sure to restart the lock manager and data sites (```Control c```) between each scenario/input file. 
    
##### On a local machine**
* Initialize 5 VMs on your local machine and obtain their IP addresses
* Initialize MySQL database instances on 4 of the VMs
* Clone this repository intoa all 5 VMs
* Choose what port your want the lock manager to listen on. Currently, it is listening on port 8001 but you can [change](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L208) that if you would like
* Change the IP address in [client.py](https://github.com/dhu5432/2PL/blob/master/client.py#L102) to connect the IP address of the VM that is to be the lock manager
* Change the MySQL IP address in each of the client.py's to reflect the local IP address of the MySQL databases you created. [Here](https://github.com/dhu5432/2PL/blob/master/client.py#L28) and [here](https://github.com/dhu5432/2PL/blob/master/client.py#L55). My code assumes that there already exists a database called ```cs542``` in each of the MySQL databases. It also assumes that the user is ```root``` and the password is ```cs542```. You can change that in the code accordingly. 
* Run ```pip3 install -r Requirements.txt```
* On the VM you designate as the lock manager: Run ```python3 servercopy.py``` 
* On the VMs you designate as the data sites: Run ```python3 client.py ---input_file=input/all_same_write.txt``` where ```input/all_same_write.txt``` is the list of queries to submit to the data site

\**I HIGHLY recommend that you run my project on Google Cloud since there will be SIGNIFICANTLY less setup involved. 



