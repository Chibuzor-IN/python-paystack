from forex_python.converter import CurrencyCodes
from errors import *
import jsonpickle

class Plan():
    '''
    Plan class for making payment plans 
    '''

    __interval = None
    __interval_values = ('hourly', 'daily', 'weekly', 'monthly','annually')    
    __name = None
    __amount = None    
    __plan_code = None
    __currency = None
    __id = None
    send_sms = True
    send_invoices = True
    description = None
    
    def __init__(self, name, interval, amount, currency = 'NGN', plan_code = None, id = None, send_sms = None, send_invoices = None, description = None):        
        #Check if currency supplied is valid
        if not CurrencyCodes().get_symbol(currency.upper()):
            raise ValueError("Invalid currency supplied")

        if interval.lower() not in self.__interval_values:
            raise ValueError("Interval should be one of 'hourly', 'daily', 'weekly', 'monthly','annually' ")

        try:
            amount = int(amount)
        except ValueError:
            raise ValueError("Invalid amount")
        else:
            self.__interval = interval.lower()
            self.__name = name
            self.__interval = interval
            self.__amount = amount
            self.__currency = currency
            self.__plan_code = plan_code
            self.__id = id
            self.send_sms = send_sms
            self.send_invoices = send_invoices
            self.description = description


    @property
    def name(self):
        return self.__name

    @property
    def interval(self):
        return self.__interval

    @property
    def amount(self):
        return self.__amount

    @property
    def plan_code(self):
        return self.__plan_code

    @property
    def id(self):
        return self.__id

    @property
    def currency(self):
        return self.__currency

    @classmethod
    def fromJSON(self, data, pickled = False):
        '''
        Creates and returns a Plan object from data dict given

        Arguments :
        data : Dict containing plan information
        pickled : Bool which is true if input dict was formed with jsonpickle
        '''
        if pickled:
            plan = jsonpickle.decode(data)

            if type(plan) is Plan:
                return plan
            else:
                raise InvalidInstance('Plan')
        else:
            name = data['name']
            interval = data['interval']
            amount = data['amount']
            currency = data['currency']
            plan_code = data['plan_code']
            id = data['id']
            send_sms = data['send_sms']
            send_invoices = data['send_invoices']
            description = data['description']
            
            return Plan(name, interval, amount, currency, plan_code, id, send_sms, send_invoices, description)

    def toJSON(self):
        '''
        Converts plan object to dict
        '''
        return jsonpickle.encode(self)
                
    def __str__(self):
        
        return "%s plan" % self.name
