import serial
from time import sleep
from threading import Thread, Lock
from gotify import Gotify

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
    def __init__(self, lock, port='/dev/ttyS0', baudrate=115200, timeout=None):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.lock = lock
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ser.close()

    def transceive(self, message):
        with self.lock:
            self.ser.write(message.encode())
            self.ser.read_until()

    def receive(self):
        with self.lock:
            return self.ser.read_until().decode()[:-2]

    def data_not_available(self):
        return self.ser.in_waiting < 2

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


def serial_spit(lock):
    global dial_number
    dial_number = '0757100883'
    pin = '0000'
    with GSM(lock=lock) as g:
        cmd = input('If you would like to set the PIN type (with caps) SET.\n')
        if cmd == 'SET':
            pin = input('Please, introduce the PIN.\n')
        init(g, pin)
        while True:    
            cmd = input(f'''\nIntroduce the command:
                        c - change the phone number (now it is {dial_number})
                        d - dial
                        h - hangup
                        m - message\n\n''')
            if cmd == 'c':
                dial_number = input('Please, introduce the phone number you would like to use from now on.\n')
            elif cmd == 'd':
                g.dial(dial_number)
            elif cmd == 'h':
                g.transceive(gsm['hangup'])
            elif cmd == 'm':
                txt = input('Please, introduce the next message.\n')
                if txt == '' :
                    continue
                g.send_sms(dial_number, txt)
            else:
                print('Command not recognized')
    

def serial_digest(lock):
    last_dialing_number = 0
    gotify = Gotify(
            base_url='http://localhost:80',
            app_token='A_8APqsvE8C5Rom',
    )

    with GSM(lock=lock, timeout=.1) as g:
        while True:
            if g.data_not_available():
                continue
            data = g.receive()
            call_status = ''
            if data == 'RING':
                call_status='Ring'
                g.transceive('AT+CLCC\r\n')
                data = g.receive()
                if data.startswith('+CLCC'):
                    for x in data[len('+CLCC: '):].split(','):
                        if x.startswith('"') and x.endswith('"'):
                            last_dialing_number = x.strip('"')
                            break
                gotify.create_message(
                    message=call_status,
                    title=last_dialing_number,
                )
                print(last_dialing_number)
                print(call_status)
                print()
            elif data == 'NO CARRIER':
                call_status='Hang'
                if last_dialing_number == 0:
                    last_dialing_number = dial_number
                gotify.create_message(
                    message=call_status,
                    title=last_dialing_number,
                )
                print(last_dialing_number)
                print(call_status)
                print()
                last_dialing_number = 0
            elif data == 'BUSY':
                call_status='Busy'
                gotify.create_message(
                    message=call_status,
                    title=dial_number,
                )
                print(dial_number)
                print(call_status)
                print()
            elif data.startswith('+CMT'):
                [number,_,date,hour] = [x.strip('"') for x in data[len('+CMT: '):].split(',')]
                message = g.receive()
                message += '\n' + date + ' ' + hour
                title = number[2:]
                gotify.create_message(
                    message=message,
                    title=title,
                )
                print(title)
                print(message)
                print()


if __name__ == '__main__':
    global dial_number
    serial_lock = Lock()
    Thread(target=serial_spit, args=(serial_lock,), daemon=True).start()
    Thread(target=serial_digest, args=(serial_lock,)).start()
