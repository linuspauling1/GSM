import serial
from time import sleep

pin = '0000'
number = '0744604883'
ctrlZ = chr(26)

gsm = {
        'check':'AT',
        'sig_quality':'AT+CSQ',
        'ready':'AT+CPIN?',
        #tech details
        'manufacturer':'AT+CGMI',
        'model':'AT+CGMM',
        'imsi':'AT+CIMI',
        'iccid':'AT+CCID',
        'net_reg_stat':'AT+CREG?',
        'scan_networks':'AT+COPS=?',
        'apn':'AT+CGDCONT?',
        'operator':'AT+COPS?',
        #tackling with GSM
        'check_sms':'AT+CMGF=1',
        'list_sms':'AT+CMGL="ALL"',
        'dial_last':'ATDL',
        'hangup':'ATH',
        'find_number':'AT+CNUM',
        'answer':'ATA',
    }

for key, value in gsm.items():
    gsm[key] = value + '\n'


class GSM:
    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        self.ser = serial.Serial(port, baudrate)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ser.close()

    def transceive(self, message):
        self.ser.write(message.encode())
        self.ser.read_until()

    def receive(self):
        return self.ser.read_until().decode()[:-2]

    def auto_answer(self, accept):
        self.transceive('ATS0=' + accept + '\n')

    def dial(self, number):
        self.transceive('ATD' + number + ';\n')

    def send_sms(self, number, text):
        self.transceive('AT+CMGS=' + '"' + number + '"' + '\n' + text + ctrlZ)

    def unlock_enable(self, status):
        if status:
            val = '1'
        else:
            val = '0'
        self.transceive('AT+CFUN=' + val + '\n')
        while True:
            answer = self.receive()
            if answer == '+CPIN: SIM PIN':
                print('Modem powered!')
            elif answer == 'OK':
                break

    def unlock_sim(self, pin):
        self.transceive('AT+CPIN=' + pin + '\n')
        while True:
            response = self.receive()
            if response == 'ERROR':
                raise Exception('Incorrect PIN!')
            elif response == 'OK':
                print('SIM activated!')
                break

    def wait(self, delay):
        self.transceive('WAIT=' + delay + '\n')

def init(g, pin):
    g.transceive(gsm['ready'])
    if g.receive() != '+CPIN: READY':
        g.unlock_enable(True)
        g.unlock_sim(pin)
    sleep(3)
    g.transceive(gsm['check_sms'])
    while True:
        response = g.receive()
        if response == 'ERROR':
            print('Cannot send SMS!')
            break
        elif response == 'OK':
            print('Ready for sending SMS!')
            break

with GSM() as g:
    init(g, pin)
    while True:
        txt = input('Please, introduce the next message.\n')
        if txt is None:
            break
        g.send_sms(number, txt)