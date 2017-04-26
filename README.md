# python-paystack

Python API wrapper for paystack ( https://paystack.com/ )

# Installation

pip install python-paystack

# Configuration

To get started, import PaystackConfig from python_paystack.paystack_config and instantiate your public and secret keys.
Other settings which are instatiated by defualt include the paystack api url (PAYSTACK_URL), PASS_ON_TRANSACTION_COST which determines if the cost per transaction is passed to the end user, LOCAL_COST and INTL_COST are the paystack charges for local and international cards respectively.

```python
from python_paystack.paystack_config import PaystackConfig

PaystackConfig.SECRET_KEY  = PAYSTACK_SECRET_KEY
PaystackConfig.PUBLIC_KEY = PAYSTACK_PUBLIC_KEY

``` 

# Usage

Most of the library's functionality lies in the managers.py file which contains the TransactionsManager, CustomersManager, PlanManager and the TransfersManager.

The Manager classes handle every direct interaction with the Paystack API.

# Transactions

You can initialize transactions using all 3 methods supported by paystack i.e Standard, Inline and Inline Embed.
Both the inline and inline embed methods return a dictionary of values while the standard method returns a Transaction object which contains an authorization url.

**Starting and verifying a standard transaction**

```python
from python_paystack.transactions import Transaction
from python_paystack.managers import TransactionsManager

transaction = Transaction(2000, 'email@test.com')
transaction_manager = TransactionsManager()
transaction = transaction_manager.initialize_transaction('STANDARD', transaction)
#Starts a standard transaction and returns a transaction object

transaction.authorization_url
#Gives the authorization_url for the transaction

#Transactions can easily be verified like so
transaction = transaction_manager.verify_transaction(transaction)

``` 

**Starting an inline transaction**
```python
transaction_manager.initialize_transaction('INLINE', transaction)

```

**Starting an inline embed transaction**
```python
transaction_manager.initialize_transaction('INLINE EMBED', transaction)
```




# Customers

**Registering a customer with paystack**

A customer can be registered using the CustomersManager.create_customer method which accepts a Customer object as an argument.
All the customer information to be sent to paystack is taken from the Customer object.
Misc. data can also be sent using the meta argument.
```python
from python_paystack.managers import CustomersManager
from python_paystack.customers import Customer

customer = Customer('test@email.com')
customer_manager = CustomersManager()
customer_manager.create_customer(customer)
```

**Getting existing customers**
```python
customer_manager = CustomersManager()
customer_manager.get_customers() 
#Returns a list containing every customer

customer_manager.get_customer(id) 
#Returns customer with the specified id
```



# Transfers

**Making a transfer with paystack**
```python
from python_paystack.transfers import Transfer
from python_paystack.managers import TransfersManager

transfer = Transfer(2000, "RCP_123456")
transfer_manager = TransfersManager()
transfer = transfer_manager.initiate_transfer(transfer)


```


# TODO : 

Tests

