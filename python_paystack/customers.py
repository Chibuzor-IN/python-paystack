import jsonpickle
import validators
from .errors import *

class Customer():
    '''
    Customer class that holds customer properties 
    '''

    phone = None
    email = None
    customer_code = None
    risk_action = None
    first_name = None
    last_name = None
    id = None
    
    def __init__(self, email, first_name = None, last_name = None, phone = None, risk_action = None, id = None):
        if validators.email(email):
            self.email = email
            self.first_name = first_name
            self.last_name = last_name
            self.phone = phone
            self.risk_action = risk_action
            self.id = id
        else:
            raise InvalidEmailError

    @classmethod
    def fromJSON(self, data, pickled = False):
        if pickled : 
            customer = jsonpickle.decode(data)
            if type(customer) is Customer:
                return customer
            else:
                raise InvalidInstance('Customer')
        else:
            email = data['email']
            first_name = data['first_name']
            last_name = data['last_name']
            phone = data['phone']
            risk_action = data['risk_action']
            id = data['id']

            return Customer(email, first_name, last_name, phone, risk_action, id)

    def toJSON(self):
        return jsonpickle.encode(self)
