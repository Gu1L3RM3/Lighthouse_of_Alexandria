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
    def add_total_values(self,name:str,total_values:dict):
        if name not in self._circuits_values:
            self._circuits_values[name] = {}
        self._circuits_values[name]['total_values'] =  total_values

    def add_circuit_values(self,name:str,values:dict):
        if name not in self._circuits_values:
            self._circuits_values[name] = {}
        self._circuits_values[name]['resistor_values'] = values
    def get_total_values(self, name: str) -> dict | None:
        circuit_data = self._circuits_values.get(name)
        
        if circuit_data is None:
            return None
            
        return circuit_data['total_values']

    def get_circuit_values(self, name: str) -> dict | None:
        circuit_data = self._circuits_values.get(name)
        
        if circuit_data is None:
            return None
            
        return circuit_data['resistor_values']
    
    def random_list_resistors(self,amount:int)->list[str]:
        resistors_list:list[str] =  list(COMERCIAL_RESISTORS.keys())
        resistors_result=sample(resistors_list,amount)

        return resistors_result

        

    