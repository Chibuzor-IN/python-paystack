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

Most of the library's functionality lies in the managers.py file which contains the PaymentManager, CustomersManager, PlanManager and the TransactionsManager.

The Manager classes handle every direct interaction with the Paystack API.

Starting and verifying transactions is handled by the PaymentManager which is designed to handle one transaction with a customer.
When PaymentManager.start_transaction is called, it returns a paystack url which the user is to be redirected to 
After a transaction is confirmed, the details are saved as member variables of the PaymentManager object . 
Charging customers with an existing authorization is handled by the TransactionsManager.

# Payments

You can initialize transactions using all 3 methods supported by paystack i.e Standard, Inline and Inline Embed.
Using the standard method to start a transaction will return a paystack url where end users can enter card details.
Both the inline and inline embed methods return a dictionary of values.

**Starting and verifying a standard transaction**

```python
from python_paystack.managers import PaymentManager

payment_manager = PaymentManager(20000, 'test@email.com')
payment_manager.start_transaction('STANDARD')
#Starts a standard transaction and returns a paystack url

#Payments can be verified using their reference
payment_manager.verify_transaction(payment_manager.reference)

``` 

**Starting an inline transaction**
```python
payment_manager.start_transaction('INLINE')

```

**Starting an inline embed transaction**
```python
payment_manager.start_transaction('INLINE EMBED')
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
customer_manager.get_customers() #Returns a list containing every customer

customer_manager.get_customer(id) #Returns customer with the specified id
```


# TODO : 

Tests

