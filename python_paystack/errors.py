#from requests import RequestException, ConnectionError

class Error(BaseException):
    pass

class InvalidInstance(Error):
    
    message = 'Not a valid instance of type : '
    manager = ''

    def __init__(self, manager):
        self.manager = manager

    def __str__(self):
        return '%s %s' % (self.message, self.manager)
   

class APIConnectionFailedError(Error):
    message = ''

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class InvalidEmailError(Error):
    message = "Invalid email address"

    def __str__(self):
        return self.message


class URLValidationError(Error):
    '''
    URLValidationError Excpetion class for invalid urls

    Attributes:
    message : Error description
    '''
    
    message = 'Invalid URL'  
        
    def __str__(self):
        return self.message
