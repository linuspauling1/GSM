import re

class TimeStamp:
    def __init__(self,day:str,month:str,year:str,hour:str,minute:str,second:str,gmt:str):
        for i in day,month,year,hour,minute,second:
            if re.search('^[0-9]{2}$',i) is None:
                raise TypeError('First 6 argument must be 2-digit strings')
        if re.search('^[+|-][0-9]{2}$',gmt) is None:
            raise TypeError('GMT must be a string with the format: <+/-><digit><digit>' + gmt)
        self.day = day
        self.month = month
        self.year = year
        self.hour = hour
        self.minute = minute
        self.second = second
        self.gmt = gmt

    def __str__(self):
        return f'''\
Date (dd/mm/yy): {self.day}/{self.month}/{self.year}
Time (hh/mm/ss): {self.hour}:{self.minute}:{self.second}, GMT: {self.gmt}\
        '''