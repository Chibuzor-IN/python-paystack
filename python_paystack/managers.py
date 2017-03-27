from .paystack_config import *
from .errors import *
from .customers import Customer
from .plans import Plan
from .filters import Filter
import requests
import json
import jsonpickle
import validators
import math

class Manager():
    '''
    Abstract base class for 'Manager' Classes
    '''

    PAYSTACK_URL = ""
    SECRET_KEY = ""

    decoder = json.JSONDecoder()

    def __init__(self, *args, **kwargs):
        if type(self) is Manager:
            raise TypeError("Can not make instance of abstract base class")

        if not PaystackConfig.SECRET_KEY or not PaystackConfig.PUBLIC_KEY:
            raise ValueError("No secret key or public key found, assign values using PaystackConfig.SECRET_KEY = SECRET_KEY and PaystackConfig.PUBLIC_KEY = PUBLIC_KEY")

        self.PAYSTACK_URL = PaystackConfig.PAYSTACK_URL
        self.SECRET_KEY = PaystackConfig.SECRET_KEY


    def get_content_status(self, content):
        '''
        Method to return the status and message from an API response

        Arguments :
        content : Response as a dict
        '''

        if  not type(content) is dict:
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

    def build_request_args(self, data = {}):
        '''
        Method for generating required headers.
        Returns a tuple containing the generated headers and the data in json.

        Arguments : 
        data(Dict) : An optional data argument which holds the body of the request.
        '''
        headers = {
                        'Authorization' : 'Bearer %s' % self.SECRET_KEY,
                        'Content-Type' : 'application/json',
                        'cache-control' : 'no-cache'
                      }

        data = json.dumps(data)
        
        return (headers, data)

    def toJSON(self):
        '''
        Method for serializing an instance of a class
        '''
        return jsonpickle.encode(self)

class PaymentManager(Manager):
    '''
    PaymentManager class that handles every part of a transaction

    Attributes:
    __amount : Transaction cost
    __email : Buyer's email
    __reference
    __authorization_url
    card_locale : Card location for application of paystack charges
    '''

    LOCAL_COST = PaystackConfig.LOCAL_COST
    INTL_COST = PaystackConfig.INTL_COST
    PASS_ON_TRANSACTION_COST = PaystackConfig.PASS_ON_TRANSACTION_COST

    __amount = None
    __email = None
    __reference = None
    __access_code = None
    __authorization_url = None
    __endpoint = '/transaction'
    card_locale = None

    def __init__(self,amount : int, email, reference = '', access_code = '', authorization_url = '', card_locale = 'LOCAL', endpoint  = '/transaction'):
        super().__init__(self)
        try:
            amount = int(amount)
        except ValueError as error:
            raise ValueError("Invalid amount. Amount(in kobo) should be an integer")
            #Error message
        else:
            #Check if the provided email is valid
            if validators.email(email):
                self.__amount = amount
                self.__email = email
                self. __reference = reference
                self.__access_code = access_code
                self.__authorization_url = authorization_url
                self.card_locale = card_locale
            else:
                raise InvalidEmailError



    #Transaction amount property
    @property
    def amount(self):
        return self.__amount

    #Transaction email property
    @property
    def email(self):
        return self.__email

    @property
    def authorization_url(self):
        return self.__authorization_url

    @property
    def reference(self):
        return self.__reference

    @property
    def access_code(self):
        return self.access_code

    def full_transaction_cost(self, locale):
        '''
        Adds on paystack transaction charges and returns updated cost

        Arguments:
        locale : Card location (LOCAL or INTERNATIONAL)
        '''
        if self.amount:
            if locale not in ('LOCAL', 'INTERNATIONAL'):
                raise ValueError("Invalid locale, locale should be either 'LOCAL' or 'INTERNATIONAL' ")
            else:
                locale_cost = {'LOCAL' : self.LOCAL_COST, 'INTERNATIONAL' : self.INTL_COST }

                cost = self.amount / (1 - locale_cost[locale])

                return math.ceil(cost)

        else:
            raise AttributeError("Amount not set")

    def start_transaction(self, callback_url = '', endpoint = '/initialize', plan_code = None):
        '''
        Initializes a paystack transaction.
        Returns an authorization url which points to a paystack form to verify card details and make the payment.

        Arguments:
        callback_url : URL paystack redirects to after a user enters their card details
        endpoint : Paystack API endpoint for intializing transactions
        '''


        if self.PASS_ON_TRANSACTION_COST:
            self.__amount = self.full_transaction_cost(self.card_locale)

        amount = self.__amount
        email = self.__email

        data = {'amount' : amount , 'email' : email}
        if plan_code:
            data['plan'] = plan_code
        if callback_url:
            #Check if callback_url is a valid url
            if validators.url(callback_url):
                data['callback_url'] = callback_url
                headers, data = self.build_request_args(data)

            else:
                raise URLValidationError

        else:
            #Use callback provided on paystack dashboard
            headers, data = self.build_request_args(data)


        url = self.PAYSTACK_URL + self.__endpoint + endpoint
        response = requests.post(url, headers = headers, data = data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        #status = True for a successful connection
        if status:
            data = content['data']
            self.__reference = data['reference']
            self.__access_code = data['access_code']
            self.__authorization_url = data['authorization_url']
            return self.__authorization_url

        else:
            #Connection failed
            raise APIConnectionFailedError(message)



    def verify_transaction(self, reference, endpoint = '/verify/'):
        '''
        Verifies a payment using the transaction reference.

        Arguments:
        endpoint : Paystack API endpoint for verifying transactions
        '''

        endpoint += reference
        url = self.PAYSTACK_URL + self.__endpoint + endpoint

        headers,_ = self.build_request_args()
        response = requests.get(url, headers = headers)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    @classmethod
    def fromJSON(self, data):
        '''
        Class method for converting JSON Object to PaymentManager Object

        Arguments:
        data : JSON serialized PaymentManager object
        '''

        manager_object = jsonpickle.decode(data)

        if type(manager_object) is PaymentManager:
            return manager_object

        else:
            raise InvalidInstance('PaymentManager')


    def __str__(self):
        return "Payment manager for %s" % (self.email)



class CustomersManager(Manager):
    '''
    CustomersManager class which handels actions for Paystack Customers

    Attributes :
    __endpoint : Paystack API endpoint for 'customers' actions

    '''
    __endpoint = None

    def __init__(self, endpoint = '/customer'):
        super().__init__(self)
        self.__endpoint = endpoint

    def create_customer(self, customer : Customer, meta = {}):
        '''
        Method for creating a new customer.

        Arguments :
        email  : Customer's email address
        first_name (optional)
        last_name (optional)
        meta : Dict which can contain additional customer information
        '''

        if not type(customer) is Customer:
            raise TypeError("customer argument should be an instance of the Customer class")

        if validators.email(customer.email):
            data = {'email' : customer.email}

            if first_name:
                data['first_name'] = customer.first_name

            if last_name:
                data['last_name'] = customer.last_name

            if meta:
                data['metadata'] = meta

            headers, data = self.build_request_args(data)

        else:
            raise InvalidEmailError


        response = requests.post(self.PAYSTACK_URL + self.__endpoint, headers = headers, data = data)

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
        headers, data = self.build_request_args()

        response  = requests.get(self.PAYSTACK_URL + self.__endpoint, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status : 
            return content['data']

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
        response = requests.get(url, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status :
            customer = Customer.fromJSON(content['data'])
            return customer
        else:
            raise APIConnectionFailedError(message)

    def update_customer(self, id, data):
        '''
        Method for updating an existing customer

        Arguments : 
        id : Customer id
        data : Dict which contains the values to be updated as keys and the updated information as the values

        '''
        headers, data = self.build_request_args(data)
        url = "%s%s/%s" % (self.PAYSTACK_URL, self.__endpoint, id)

        response = requests.put(url, headers = headers, data = data)
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

            response = requests.post(url, headers = headers, data = data)

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
        response = requests.post(url, headers = headers, data = data)

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

    def __init__(self, endpoint = '/plan'):
        super().__init__(self)
        self.__endpoint = endpoint

    def create_plan(self, plan : Plan):
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
    
    __endpoint = '/transaction'
    def __init__(self, endpoint = '/transaction'):
        super().__init__(self)
        self.__endpoint = endpoint

    def charge_authorization(self, authorization_code, amount, email, plan_code = None):
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

        response = requests.post(self.PAYSTACK_URL + self.__endpoint, headers = headers, data = data)         
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

        response = requests.get(self.PAYSTACK_URL + self.__endpoint, headers = headers)

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
        response = requests.get(url, headers = headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)

    
    def filter_transactions(self, amount_range : range, transactions):
        
        results = []
        for transaction in transactions:
            if Filter.filter_amount(amount_range, transaction):
                results.append(transaction)

        return results