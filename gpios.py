import gpiod
import serial
import re
from threading import Thread, Lock
from time import sleep

mutex = Lock()

ser = serial.Serial(
   port='/dev/ttyUSB2',
   baudrate=115200,
)

msg_led_pin = 12
rng_led_pin = 21

chip = gpiod.Chip('gpiochip4')

msg_led_line = chip.get_line(msg_led_pin)
msg_led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
rng_led_line = chip.get_line(rng_led_pin)
rng_led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)

rng_led_line.release
msg_led_line.release

def receiver():
    while True:
        if ser.in_waiting > 1:
            rng_led_line.set_value(0)
            with mutex:
                txt = ser.readline().decode()[:-2]
            if txt == 'RING':
                rng_led_line.set_value(1)
                with mutex:
                    ser.readline()
                    x = ser.readline().decode()[:-2]
                x = re.search('^\+CLIP: "\+[0-9]*"', x).group()
                x = x[len('+CLIP: '):].strip('"')
                print(x[2:], ' is trying to reach you!')
            elif txt == 'NO CARRIER':
                print('Busy number')
            elif txt.startswith('VOICE CALL: END: '):
                with mutex:
                    ser.readline()
                    ser.readline()
                print('Call ended')
            elif txt.startswith('+CMT'):
                msg_led_line.set_value(1)
                x = re.search('^\+CMT: "\+[0-9]*"', txt).group()
                x = x[len('+CMT: '):].strip('"')
                print(x[2:], ' sent the next message to you:')
                with mutex:
                    x = ser.readline().decode()[:-2]
                print(x)
            else:
                sleep(.1)

def transmitter():
    while True:
        peer = '0744604883'
        x = input('''
            V - see current recipient\'s number
            N - change current recipient\'s number
            C - call
            M - message
            A - answer
            H - hang up
            R - message read
            ''')
        if x == 'V':
            print('\n'+peer)
        elif x == 'N':
            peer = input('Introduce the new number of the callee: ')
        elif x == 'C':
            with mutex:
                ser.write(('ATD'+peer+';\r\n').encode())
        elif x == 'M':
            txt = input('Message: ')
            ctrl_Z = chr(26)
            content = f'at+cmgs="{peer}"\r\n'
            with mutex:
                ser.write(content.encode())
                sleep(.5)
                content=f'{txt}{ctrl_Z}'
                ser.write(content.encode())
        elif x == 'A':
            with mutex:
                ser.write(('ATA\r\n').encode())
        elif x == 'H':
            with mutex:
                ser.write(('AT+CHUP\r\n').encode())
        elif x == 'R':
            msg_led_line.set_value(0)
        else:
            print('Wrong command')

Thread(target=receiver).start()
Thread(target=transmitter).start()