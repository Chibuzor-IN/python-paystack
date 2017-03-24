import jsonpickle
from errors import *

class Customers():
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
    
    def __init__(self):
        pass

    @classmethod
    def fromJSON(self, data):
        return jsonpickle.decode(data)

    def toJSON(self):
        pass
