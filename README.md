# python-paystack

Python API wrapper for paystack

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

Starting and verifying transactions is handled by the PaymentManager which is designed to handle one transaction with a customer.
When PaymentManager.start_transaction is called, it returns a paystack url which the user is to be redirected to 
After a transaction is confirmed, the details are saved as member variables of the PaymentManager object . 
Charging customers with an existing authorization is handled by the TransactionsManager.

# Starting a Transaction
```python
payment_manager = PaymentManager(20000, 'test@email.com')
payment_manager.start_transaction()
#Starts a transaction and returns a paystack url

#Payments can be verified using their reference
payent_manager.verify_transaction(payment_manager.reference)

``` 

