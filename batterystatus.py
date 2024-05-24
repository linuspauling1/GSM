import re

class BatteryStatus:
    def __init__(self,voltage:str,level:str,status:str):
        for i in voltage, level:
            if re.search('^[0-9]+$',i) is None:
                raise TypeError('First two arguments must be 2-digit strings')
        self.voltage = voltage
        self.level = level
        self.status = status

    def __str__(self):
        return f'Voltage: {self.voltage}mV\nLevel  : {self.level}%\nStatus : {self.status}'