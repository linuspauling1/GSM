import serial
import re
from threading import Thread, Lock
from time import sleep

mutex = Lock()

ser = serial.Serial(
   port='/dev/ttyS0',
   baudrate=115200,
)

def transmit_cmd(cmd):
    ser.write((cmd+"\n").encode())
    #prevent reading the command itself
    ser.readline()

def receive_cmd():
    #prevent reading the newline character
    return ser.readline().decode()[:-2]

def set_rf():
    transmit_cmd('at+cfun?')
    msg = receive_cmd()
    if msg == '+CFUN: 1':
        return
    transmit_cmd('at+cfun=1')
    #command's execution may take longer, thus it has to be checked
    while receive_cmd() != '+CPIN: SIM PIN':
        pass

#returns status regarding the completion of the operation
def set_pin(pin='0000'):
    transmit_cmd('at+cpin?')
    msg = receive_cmd()
    if msg == '+CPIN: READY':
        return True
    transmit_cmd(f'at+cpin={pin}')
    msg = receive_cmd()
    if msg == 'ERROR':
        return False
    elif msg == 'OK':
        #dump serial buffer
        while msg != 'Call Ready':
            msg = receive_cmd()
        return True

def initialize_gsm():
    #set to spit the new messages instead of storing them 
    transmit_cmd('at+cnmi=1,2,2,1,1')
    #set SMS mode as text
    transmit_cmd('at+cmgf=1')
    #show SMS params, like time
    transmit_cmd('at+csdh=1')
    #show the incoming call parameters like caller number
    transmit_cmd('at+clip=1')

def send_sms(text, number):
    ctrl_Z = chr(26)
    content=f'at+cmgs="{number}"\n{text}{ctrl_Z}'
    with mutex:
        ser.write(content.encode())

def read_data():
    if ser.in_waiting > 1:
        with mutex:
            msg = receive_cmd()
        if msg.startswith('+CMT: '):
            caller = re.search(r'"\+[0-9]*"',msg).group()
            moment = re.search(r'"[0-9]{2}/[0-9]{2}/[0-9]{2},[0-9]{2}:[0-9]{2}:[0-9]{2}\+[0-9]*"',msg).group()
            calendar = re.search(r'[0-9]{2}/[0-9]{2}/[0-9]{2}',moment).group()
            hour = re.search(r'[0-9]{2}:[0-9]{2}:[0-9]{2}',moment).group()
            print(f'\nFrom {caller[3:-1]} at date {calendar} and hour {hour} was sent the message:')
            print(receive_cmd())
            print('Select service (a-answer, c-call, h-hang, m-message): ',end='',flush=True)
        elif msg.startswith('+CLIP: '):
            caller_number = re.search(r'"\+?[0-9]*"',msg).group()
            print(f'\n{caller_number} is trying to reach you    ',end='',flush=True)
        elif msg == 'NO CARRIER':
            print('\nCall ended')
            print('Select service (a-answer, c-call, h-hang, m-message, n-set/view callee number): ',end='',flush=True)
        elif msg == 'BUSY':
            print('\nCall rejected')
            print('Select service (a-answer, c-call, h-hang, m-message, n-set/view callee number): ',end='',flush=True)
    else:
        sleep(.1)

def user_action_listener():
    number = '0744604883'
    while True:
        text = input('Select service (a-answer, c-call, h-hang, m-message, n-set/view callee number): ')
        if text == 'a':
            transmit_cmd('ata')
        elif text == 'c':
            transmit_cmd('atd' + number + ';')
        elif text == 'h':
            transmit_cmd('ath')
        elif text == 'm':
            sms = input('Please, provide SMS content: ')
            send_sms(text=sms,number=number)
        elif text == 'n':
            print(f'The current callee number is {number}')
            number = input('Please, provide the new callee number: ')
        else:
            print('Wrong command!')

def incoming_data_listener():
    while True:
        read_data()

if __name__ == '__main__':
    set_rf()
    set_pin()
    initialize_gsm()
    Thread(target=incoming_data_listener).start()
    Thread(target=user_action_listener).start()