### Infrastructure

The entire project run on the [Google Cloud Platform](https://cloud.google.com/) using VMs and CloudSQL instances. To request access to the
project, please give me an email to add. 

### Description of Files

```servercopy.py``` This is the centralized transaction/lock manager that holds the lock table. 

```client.py``` This is a data site that is connected to a MySQL database. Within the Google Cloud Platform, I have 4 separate VMs that have a ```client.py``` script, but with lines ```27``` and ```89``` changed because each VM/data site is connected to its own MySQL database. 

### Walkthrough of Algorithm*

The algorithm starts at a data site sending a [transaction request](https://github.com/dhu5432/2PL/blob/master/client.py#L132) message with locally identifiable transaction ID, with a list of data rows and their operations for that specific transaction. So a transaction request with the payload 

```[34, [R, 100, Balance, [W, 308, Assets, 100]]```

means that this is transaction 34 from that data site, and the transaction wants to read row 100's balance and change row 308's Assets to 100. 

The lock manager [receives the transaction request](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L113) and processes it as it sees fit. If the transaction is granted, it replies back to the data site with a [transaction granted](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L161) message. 

Once the data site [receives](https://github.com/dhu5432/2PL/blob/master/client.py#L41) the transaction granted message, it executesthe corresponding queries and responds back with an [execute](https://github.com/dhu5432/2PL/blob/master/client.py#L78) message. 

Once the lock manager [receives](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L69) the execute message. It broadcasts to the other 3 data sites the SQL queries to be executed and releases all locks associated with the current transaction request. 


*A much more detailed walkthrough of my implementation's algorithm is given in the project report, but this is to help associate the code written with each step of the algorithm.

### Output
My report mentions that "I add a multitude of ```print``` statements throughout my implementation in order to understand what the system is doing at any given time. I detail the kind of output my system gives in this section. 

#### Lock Manager Output
```i is requesting a transaction``` When some data site ```i``` sends a transaction request message to the lock manager, the lock manager outputs to the console in order to acknowledge the receipt of the transaction request. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L121)

```Transaction j from site i is a Read operation on row k, but another transaction is currently writing to it``` When data site ```i``` sends transaction ```j``` to the lock manager, the lock manager looks in the lock table and outputs if it is currently unable to grant the transaction because another transaction has a write lock on one of the rows transaction ```j``` needs a read lock for. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L132)

```Transaction j from site i is a Write operation on row k, but another transaction is currently reading or writing ot it``` When data site ```i``` sends transaction ```j``` to the lock manager, the lock manager looks in the lock table and outputs if it is currently unable to grant the transaction because another transaction is currently reading or writing to row ```j```. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L134)

```Executing transaction j from site i on all sites``` When data site ```i``` has successfully executed transaction ```j```, it sends the lock manager the SQL queries that need to be executed at all other data sites. This outputs right before the lock manager broadcasts the SQL queries to execute on the other data sites. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L134)

```Released locks used in transaction j from site i``` After the lock manager broadcasts to all data sites the SQL queries to be executed for transaction j, it releases the locks associated with transaction j and this outputs. [In the code](https://github.com/dhu5432/2PL/blob/master/servercopy.py#L82)

#### Data Site Output
```Locks for transaction i granted``` As mentioned in the report, at each data site, each transaction is given an ID. A transaction ID and a data site ID can globally identify all transactions. This output means that transaction ```i``` can now be executed on the site that outputs this statement. [In the code](https://github.com/dhu5432/2PL/blob/master/client.py#L44)

```Successfully executed transaction i``` After the locks for transaction ```i``` have been granted, it connects to the MySQL database and executes all corresponding SQL queries. Once it finishes, this statement outputs. [In the code](https://github.com/dhu5432/2PL/blob/master/client.py#L77)




