from core.settings import *
from random import sample
class CircuitManager:
    _instance = None
    def __init__(self):
        self._circuits_values = {}
    

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = CircuitManager()
        return cls._instance
    
    def add_circuit_values(self,name:str,values:dict):
        self._circuits_values[name] = values
    
    def get_circuit_values(self,name:str)->dict|None:
        return self._circuits_values.get(name,None)
    
    def random_list_resistors(self,amount:int)->list[str]:
        resistors_list:list[str] =  list(COMERCIAL_RESISTORS.keys())
        resistors_result=sample(resistors_list,amount)

        return resistors_result

        

    