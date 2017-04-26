'''
Base.py
'''
import json
import jsonpickle
from .errors import InvalidInstance

class Base():
    '''
    Abstract Base Class
    '''
    def __init__(self):
        if isinstance(self, Base):
            raise TypeError("Can not make instance of abstract base class")


    def to_json(self, pickled=True):
        '''
        Method to serialize class instance
        '''
        if pickled:
            return jsonpickle.encode(self)
        else:
            data = json.JSONDecoder().decode(jsonpickle.encode(self))
            data.pop("py/object")
            return json.dumps(data)

    @classmethod
    def from_json(cls, data, pickled=True):
        '''
        Method to return a class instance from given json dict
        '''
        class_name = cls.__name__
        class_object = None
        if pickled:
            class_object = jsonpickle.decode(data)
        else:
            py_object = str(cls).replace('<class ', '')
            py_object.replace('>', '')
            data['py/object'] = py_object
            class_object = jsonpickle.decode(data)

        if isinstance(class_object, cls):
            return class_object
        else:
            raise InvalidInstance(class_name)
