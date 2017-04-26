'''
Managers.py
'''
import requests
import math
import json
from datetime import datetime
import validators
from forex_python.converter import CurrencyCodes
from .paystack_config import PaystackConfig
from .errors import *
from .customers import Customer
from .plans import Plan
from .transfers import Transfer
from .filters import Filter
from .base import Base




class Manager(Base):
    '''
    Abstract base class for 'Manager' Classes
    '''

    PAYSTACK_URL = None
    SECRET_KEY = None
    LOCAL_COST = None
    INTL_COST = None
    PASS_ON_TRANSACTION_COST = None

    decoder = json.JSONDecoder()

    def __init__(self):
        super().__init__()
        if isinstance(self, Manager):
            raise TypeError("Can not make instance of abstract base class")

        if not PaystackConfig.SECRET_KEY or not PaystackConfig.PUBLIC_KEY:
            raise ValueError("No secret key or public key found,"
                             "assign values using PaystackConfig.SECRET_KEY = SECRET_KEY and"
                             "PaystackConfig.PUBLIC_KEY = PUBLIC_KEY")

        self.PAYSTACK_URL = PaystackConfig.PAYSTACK_URL
        self.SECRET_KEY = PaystackConfig.SECRET_KEY

        if isinstance(self, PaymentManager):
            self.LOCAL_COST = PaystackConfig.LOCAL_COST
            self.INTL_COST = PaystackConfig.INTL_COST
            self.PASS_ON_TRANSACTION_COST = PaystackConfig.PASS_ON_TRANSACTION_COST


    def get_content_status(self, content):
        '''
        Method to return the status and message from an API response

        Arguments :
        content : Response as a dict
        '''

        if  not isinstance(content, dict):
            raise TypeError("Content argument should be a dict")

        return (content['status'], content['message'])

    def parse_response_content(self, content):
        '''
        Method to convert a response's content in bytes to a string.

        Arguments:
        content : Response in bytes
        '''
        content = bytes.decode(content)
        content = self.decoder.decode(content)
        return content

    def build_request_args(self, data=None):
        '''
        Method for generating required headers.
        Returns a tuple containing the generated headers and the data in json.

        Arguments :
        data(Dict) : An optional data argument which holds the body of the request.
        '''
        headers = {'Authorization' : 'Bearer %s' % self.SECRET_KEY,
                   'Content-Type' : 'application/json',
                   'cache-control' : 'no-cache'
                  }

        data = json.dumps(data)

        return (headers, data)


class PaymentManager(Manager):
    '''
    PaymentManager class that handles every part of a transaction

    Attributes:
    amount : Transaction cost
    email : Buyer's email
    reference
    authorization_url
    card_locale : Card location for application of paystack charges
    '''

    amount = None
    email = None
    reference = None
    access_code = None
    authorization_url = None
    __endpoint = '/transaction'
    card_locale = None

    def __init__(self, amount: int, email, reference='', access_code='',
                 authorization_url='', card_locale='LOCAL'):
        super().__init__(self)
        try:
            amount = int(amount)
        except ValueError:
            raise ValueError("Invalid amount. Amount(in kobo) should be an integer")
            #Error message
        else:
            #Check if the provided email is valid
            if validators.email(email):
                self.amount = amount
                self.email = email
                self. reference = reference
                self.access_code = access_code
                self.authorization_url = authorization_url
                self.card_locale = card_locale
            else:
                raise InvalidEmailError

    def generate_reference_code(self):
        '''
        Generates a unique transaction reference code
        '''
        date = datetime.now()
        year = date.year
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        date_stamp = "%s%s%s" % (year, month, day)

        reference_code = "%s%s" % (date_stamp, hash(self.email))

        time = date.time()
        hour = time.hour
        minute = time.minute
        second = time.second

        reference_code += "%s%s%s" % (hour, minute, second)

        return reference_code

    def full_transaction_cost(self, locale):
        '''
        Adds on paystack transaction charges and returns updated cost

        Arguments:
        locale : Card location (LOCAL or INTERNATIONAL)
        '''
        if self.amount:

            if locale not in ('LOCAL', 'INTERNATIONAL'):
                raise ValueError("Invalid locale, locale should be 'LOCAL' or 'INTERNATIONAL'")

            else:
                locale_cost = {'LOCAL' : self.LOCAL_COST, 'INTERNATIONAL' : self.INTL_COST}

                cost = self.amount / (1 - locale_cost[locale])

                if cost > 250000:
                    cost = (self.amount + 100)/ (1 - locale_cost[locale])

                paystack_charge = locale_cost[locale] * cost
                #Paystack_charge is capped at N2000
                if paystack_charge > 200000:
                    cost = self.amount + 200000

                return math.ceil(cost)

        else:
            raise AttributeError("Amount not set")

    def start_transaction(self, method, callback_url='', metadata=None,
                          plan_code=None, endpoint='/initialize'):
        '''
        Initializes a paystack transaction.
        Returns an authorization url which points to a paystack form if the method is standard.
        Returns a dict containing transaction information if the method is inline or inline embed

        Arguments:
        method : Specifies whether to use paystack inline, standard or inline embed
        callback_url : URL paystack redirects to after a user enters their card details
        plan_code : Payment plan code
        endpoint : Paystack API endpoint for intializing transactions
        '''

        method = method.upper()
        if method not in ('STANDARD', 'INLINE', 'INLINE EMBED'):
            raise ValueError("method argument should be STANDARD, INLINE or INLINE EMBED")


        if self.PASS_ON_TRANSACTION_COST:
            self.amount = self.full_transaction_cost(self.card_locale)

        amount = self.amount
        email = self.email

        data = {'amount' : amount, 'email' : email, 'reference' : self.generate_reference_code(),
                'metadata' : metadata}

        if plan_code:
            data['plan'] = plan_code

        if method in ('INLINE', 'INLINE EMBED'):
            data['key'] = PaystackConfig.PUBLIC_KEY
            return data

        if callback_url:
            #Check if callback_url is a valid url
            if validators.url(callback_url):
                data['callback_url'] = callback_url

            else:
                raise URLValidationError

        headers, data = self.build_request_args(data)

        url = self.PAYSTACK_URL + self.__endpoint + endpoint
        response = requests.post(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        #status = True for a successful connection
        if status:
            data = content['data']
            self.reference = data['reference']
            self.access_code = data['access_code']
            self.authorization_url = data['authorization_url']
            return self.authorization_url

        else:
            #Connection failed
            raise APIConnectionFailedError(message)



    def verify_transaction(self, reference, endpoint='/verify/'):
        '''
        Verifies a payment using the transaction reference.

        Arguments:
        endpoint : Paystack API endpoint for verifying transactions
        '''

        endpoint += reference
        url = self.PAYSTACK_URL + self.__endpoint + endpoint

        headers, _ = self.build_request_args()
        response = requests.get(url, headers=headers)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)


    def __str__(self):
        return "Payment manager for %s" % (self.email)



class CustomersManager(Manager):
    '''
    CustomersManager class which handels actions for Paystack Customers

    Attributes :
    __endpoint : Paystack API endpoint for 'customers' actions

    '''
    __endpoint = '/customer'

    def __init__(self):
        super().__init__(self)

    def create_customer(self, customer: Customer, meta=None):
        '''
        Method for creating a new customer.

        Arguments :
        email  : Customer's email address
        customer : Customer object
        meta : Dict which can contain additional customer information
        '''

        if not isinstance(customer, Customer):
            raise TypeError("customer argument should be an instance of the Customer class")

        if validators.email(customer.email):
            data = customer.to_json(pickled=False)

            headers, _ = self.build_request_args()

        else:
            raise InvalidEmailError


        response = requests.post(self.PAYSTACK_URL + self.__endpoint, headers=headers, data=data)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:

            if message == 'Customer created':
                return content['data']
            else:
                raise ValueError("A customer with this email already exists")

        else:
            raise APIConnectionFailedError(message)


    def get_customers(self):
        '''
        Method which returns all registered customers
        '''
        headers, _ = self.build_request_args()

        response = requests.get(self.PAYSTACK_URL + self.__endpoint, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            customers = []
            for item in data:
                customer = Customer.from_json(item)
                customers.append(customer)

        else:
            raise APIConnectionFailedError(message)


    def get_customer(self, id):
        '''
        Method for getting a particular customer with the specified id

        Arguments :
        id : Customer id

        '''
        headers, data = self.build_request_args()
        url = "%s%s/%s" % (self.PAYSTACK_URL, self.__endpoint, id)
        response = requests.get(url, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            customer = Customer.from_json(content['data'])
            return customer
        else:
            raise APIConnectionFailedError(message)

    def update_customer(self, id, data):
        '''
        Method for updating an existing customer

        Arguments :
        id : Customer id
        data : Dict which contains the values to be updated as keys
                and the updated information as the values
        '''
        headers, data = self.build_request_args(data)
        url = "%s%s/%s" % (self.PAYSTACK_URL, self.__endpoint, id)

        response = requests.put(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)
        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    def set_risk_action(self, risk_action, id):
        '''
        Method for either blacklisting or whitelisting a customer

        Arguments :
        risk_action : (allow or deny)
        id : Customer id

        '''

        endpoint = '/set_risk_action'

        if risk_action not in ('allow', 'deny'):
            raise ValueError("Invalid risk action")

        else:
            data = {'customer' : id, 'risk_action' : risk_action}
            headers, data = self.build_request_args(data)
            url = "%s%s" % (self.PAYSTACK_URL + self.__endpoint, endpoint)

            response = requests.post(url, headers=headers, data=data)

            content = response.content
            content = self.parse_response_content(content)

            status, message = self.get_content_status(content)

            if status:
                return content['data']
            else:
                raise APIConnectionFailedError(message)

    def deactive_authorization(self, authorization_code):
        '''
        Method to deactivate an existing authorization

        Arguments :
        authorization_code : Code for the transaction to be deactivated

        '''
        data = {'authorization_code' : authorization_code}
        headers, data = self.build_request_args(data)

        url = "%s/deactivate_authorization" % (self.PAYSTACK_URL + self.__endpoint)
        response = requests.post(url, headers=headers, data=data)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)




class PlanManager(Manager):
    '''
    Plan Manager class
    '''

    __endpoint = '/plan'

    def __init__(self, endpoint='/plan'):
        super().__init__(self)
        self.__endpoint = endpoint

    def create_plan(self, plan: Plan):
        '''
        Method for creating plans

        Arguments:
        plan : Plan object

        '''
        url = self.PAYSTACK_URL + self.__endpoint

        data = {
            'name' : plan.name,
            'interval' : plan.interval,
            'amount' : plan.amount
            }

        headers, data = self.build_request_args(data)

        response = requests.post(url, headers = headers, data = data)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    def get_plans(self):
        headers, data = self.build_request_args()
        response = requests.get(self.PAYSTACK_URL + self.__endpoint, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)


    #Implement as class method to return a Plan object
    def get_plan(self, id):
        headers, data = self.build_request_args()

        url = "%s%s/%s" % (self.PAYSTACK_URL,self.__endpoint, id)
        response = requests.get(url, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)



class TransactionsManager(Manager):
    '''
    TransactionsManager class
    '''
    __endpoint = '/transaction'
    def __init__(self, endpoint = '/transaction'):
        super().__init__(self)
        self.__endpoint = endpoint

    def charge_authorization(self, authorization_code, amount, email, plan_code=None):
        data = {'authorization_code' : authorization_code}
        if plan_code:
            data['plan'] = plan_code

        try:
            amount = int(amount)
        except ValueError as error:
            raise ValueError("Invalid amount. Amount(in kobo) should be an integer")
        else:
            if validators.email(email):
                data['amount'] = amount
                data['email'] = email
                headers, data = self.build_request_args(data)
            else:
                raise InvalidEmailError

        response = requests.post(self.PAYSTACK_URL + self.__endpoint, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        #status = True for a successful connection
        if status:
            return content['data']
        else:
            #Connection failed
            raise APIConnectionFailedError(message)
        
    def get_total_transactions(self):
        '''
        Get total amount recieved from transactions
        '''
        headers, data = self.build_request_args()
        url = self.PAYSTACK_URL + self.__endpoint
        url += '/totals'
        response = requests.get(url, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    def get_transactions(self):
        '''
        Gets all transactions
        '''
        headers, data = self.build_request_args()

        response = requests.get(self.PAYSTACK_URL + self.__endpoint, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    def get_transaction(self, id):
        '''
        Gets transaction with the specified id
        '''
        headers, data = self.build_request_args()

        url = self.PAYSTACK_URL + self.__endpoint
        url += '/%s' % (str(id))
        response = requests.get(url, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)


    def filter_transactions(self, amount_range: range, transactions):
        '''
        Returns all transactions with amounts in the given amount_range
        '''
        results = []
        for transaction in transactions:
            if Filter.filter_amount(amount_range, transaction):
                results.append(transaction)

        return results


class TransfersManager(Manager):
    '''
    TransfersManager class
    '''

    __endpoint = '/transfer'
    def __init__(self, endpoint='/transfer'):
        super().__init__(self)
        self.__endpoint = endpoint


    def initiate_transfer(self, transfer: Transfer):
        '''
        Method to start a transfer to a bank account.
        '''

        data = transfer.to_json(pickled=False)


        headers, data = self.build_request_args(data)

        url = self.PAYSTACK_URL + self.__endpoint
        response = requests.post(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            transfer.status = data['status']
            transfer.transfer_code = data['transfer_code']
            return transfer

        else:
            #Connection failed
            raise APIConnectionFailedError(message)


    def get_transfers(self):
        '''
        Method to get all paystack transfers
        '''
        headers, data = self.build_request_args()

        url = self.PAYSTACK_URL + self.__endpoint
        response = requests.get(url, headers=headers)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            return data

        else:
            #Connection failed
            raise APIConnectionFailedError(message)

    def get_transfer(self, transfer_id):
        '''
        Method to get paystack transfer with the specified id
        '''
        headers, data = self.build_request_args()

        url = self.PAYSTACK_URL + self.__endpoint
        url += '/%s' % (transfer_id)
        response = requests.post(url, headers=headers)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            return data
        else:
            #Connection failed
            raise APIConnectionFailedError(message)

    def finalize_transfer(self, transfer_id, otp):
        '''
        Method for finalizing transfers
        '''
        transfer_id = str(transfer_id)
        otp = str(otp)

        data = {'transfer_code' : transfer_id, 'otp' : otp}
        headers, data = self.build_request_args(data)

        url = self.PAYSTACK_URL + self.__endpoint
        url += '/finalize_transfer'
        response = requests.post(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            return data

        else:
            #Connection failed
            raise APIConnectionFailedError(message)
