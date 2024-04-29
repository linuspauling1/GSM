import serial
from time import sleep
from threading import Thread, Lock
from gotify import Gotify

lock = Lock()
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

def serial_spit():
    pin = '0000'
    number = '0744604883'

    with GSM() as g:
        try:
            lock.acquire()
            cmd = ('If you would like to set the PIN press nothing but the return key.\n')
            if cmd == '':
                pin = input('Please, introduce the PIN.\n')
            init(g, pin)
        finally:
            lock.release()
            
        while True:
            try:
                lock.acquire()
                cmd = input(f'''Introduce the command:
                            c - change the phone number (now it is {number} )
                            d - dial
                            h - hangup
                            m - message\n\n''')
                if cmd == 'c':
                    number = input('Please, introduce the phone number you would like to use from now on.\n')
                elif cmd == 'd':
                    g.dial(number)
                elif cmd == 'h':
                    g.transceive(gsm['hangup'])
                elif cmd == 'm':
                    txt = input('Please, introduce the next message.\n')
                    if txt == '' :
                        break #continue
                    g.send_sms(number, txt)
            finally:
                lock.release()

def serial_digest():
    last_dialing_number = 0

    gotify = Gotify(
            base_url='http://localhost:80',
            app_token='A_8APqsvE8C5Rom',
    )
    
    with serial.Serial('/dev/ttyS0', baudrate=115200) as ser:
        while True:
            try:
                lock.acquire()

                call_status = ''
                data = ser.read_until().decode()

                if data == 'RING\r\n':
                    call_status='Ring'
                    ser.write(b'AT+CLCC\r\n')
                    ser.read_until()
                    data = ser.read_until().decode()
                    if data.startswith('+CLCC'):
                        for x in data[len('+CLCC: '):-len('\r\n')].split(','):
                            if x.startswith('"') and x.endswith('"'):
                                last_dialing_number = x.strip('"')
                    gotify.create_message(
                        message=call_status,
                        title=last_dialing_number,
                    )
                    #print(last_dialing_number)
                    #print(call_status)
                    #print()
                elif data == 'NO CARRIER\r\n':
                    call_status='Hang'
                    gotify.create_message(
                        message=call_status,
                        title=last_dialing_number,
                    )
                    #print(last_dialing_number)
                    #print(call_status)
                    #print()
                elif data.startswith('+CMT'):
                    [number,_,date,hour] = [x.strip('"') for x in data[len('+CMT: '):-len('\r\n')].split(',')]
                    message = ser.read_until(b'\r\n').decode()[:-2]
                    message += '\n' + date + ' ' + hour
                    title = number[2:]
                    #print(title)
                    #print(message)
                    #print()
                    gotify.create_message(
                        message=message,
                        title=title,
                    )
            finally:
                lock.release()


if __name__ == "__main__":
  thread1 = Thread(target=serial_spit)
  thread2 = Thread(target=serial_digest)

  thread1.start()
  thread2.start()

  thread1.join()
  thread2.join()

  print("Main thread: Done")