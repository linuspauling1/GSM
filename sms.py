from timestamp import TimeStamp

class SMS:
    def __init__(self,number:str,date_time:TimeStamp,message:str):
        self.number = number
        self.date_time = date_time
        self.message = message

    def __str__(self):
        return f'From: {self.number}\n{str(self.date_time)}\n{self.message}'