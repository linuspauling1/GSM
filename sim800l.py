from time import sleep
from timestamp import TimeStamp
from sms import SMS
from batterystatus import BatteryStatus
from gsmregdata import GSMRegData
import serial
import re

ctrlZ = chr(26)
sms_max_length = 160

class SIM800L:
    def __init__(self, port = '/dev/ttyS0',baudrate=115200, timeout=.2): #TODO: implement thread locks
        self.ser = serial.Serial(port=port,baudrate=baudrate,timeout=timeout)

    def transmit(self, cmd: str):
        cmd_enc = (cmd + '\n').encode()
        self.ser.write(cmd_enc)
        self.ser.readline() # avoid receiving transmitted command

    def receive(self):
        res_enc = self.ser.readline()[:-2]
        return res_enc.decode()

    def is_at_ok(self):
        self.transmit('AT')
        if self.receive() == 'OK':
            return True
        return False
    
    def wait(self, delay: str):
        self.transmit('WAIT'+delay)

    def get_signal_quality(self):
        self.transmit('AT+CSQ')
        resp = self.receive()
        if resp.startswith('+CSQ'):
            rssi = re.search('[0-9]+', resp).group()
            return 'RSSI: ' + rssi
        else:
            raise Exception('CSQ Inappropiate response: ' + resp)

    def check_sms_cnmi(self):
        self.transmit('AT+CNMI?')
        resp = self.receive()
        if resp.startswith('+CNMI'):
            x = re.findall('[0-9]',resp)
            print(resp)
            return x[1]
        else:
            raise Exception('CNMI Inappropiate response: ' + resp)

    def set_sms_cnmi(self):
        self.transmit('AT+CNMI=1,2,2,1,1')

    def answer(self):
        self.transmit('ATA')

    def hangup(self):
        self.transmit('ATH')

    def dial_last_number(self):
        self.transmit('ATDL')

    def dial(self, number: str):
        self.transmit('ATD' + number + ';')

    def get_incoming_call_number(self):
        self.transmit('AT+CLCC')
        for i in range(100):
            '''
            not available current call data 
            for a long time => no incoming call => quit 
            don't keep the loop alive anymore
            ''' 
            if self.ser.in_waiting > 1:
                resp = self.receive()
                if resp.startswith('+CLCC'):
                    number = re.search('"[^,]+"',resp).group()
                    number = number.strip('"')
                    return number
            else:
                sleep(.1) # let the other threads alive
        return None

    def is_show_sms_params(self):
        self.transmit('AT+CSDH?')
        resp = self.receive()
        if resp.startswith('+CSDH'):
            x = re.search('[0-9]',resp).group()
            return x == '1'
        else:
            raise Exception('+CSDH Inappropiate response ' + resp)

    def set_show_sms_params(self, set=True):
        if set:
            self.transmit('AT+CSDH=1')
        else:
            self.transmit('AT+CSDH=0')

    def show_ser_async_data(self): # TODO: rewrite to return something
        if not self.is_show_sms_params(): # TODO: moved in an init method
            self.set_show_sms_params()
        call_status_map = {
            'RING': 'Ringing',
            'NO CARRIER': 'Call or ring ended by peer',
            'BUSY': 'Call declined by callee'
        }
        while True:
            if self.ser.in_waiting > 1:
                resp = self.receive()
                if resp in call_status_map:
                    print(call_status_map[resp]) # TODO: get rid of this
                elif resp.startswith('+CMT'):
                    x = re.findall('[^,]+',resp[len('+CMT: '):])
                    x = [i.strip('"') for i in x]
                    x = [i for i in x if i != '']
                    number = x[0][2:]
                    date = x[1]
                    time = x[2]
                    no_chars = int(x[-1])
                    y,m,d = re.findall('[0-9]{2}',date)
                    hr,min,sec,gmt = re.findall('[+]?[0-9]{2}',time)
                    msg = self.ser.read(no_chars).decode()
                    print(SMS(number,TimeStamp(d,m,y,hr,min,sec,gmt),msg))
            else:
                sleep(.1) # let the other threads alive

    def get_battery_level(self):
        status_map = {'0':'not charging', '1':'charging', '2':'charing finished'}
        self.transmit('AT+CBC')
        resp = self.receive()
        if resp.startswith('+CBC'):
            status, level, voltage = re.findall('[0-9]+',resp)
            return BatteryStatus(voltage,level,status_map[status])
        else:
            raise Exception('+CBC Inappropiate response: ' + resp)
            
    def send_sms(self, number: str, sms: str):
        text = sms
        if len(sms) > sms_max_length:
            res_text, text = sms[:-sms_max_length], sms[-sms_max_length:]
            self.send_sms(number,res_text)
        data = f'AT+CMGS="{number}"\n' + text + ctrlZ
        self.ser.write(data.encode())
        while self.receive() != 'OK':
            '''
            didn't check data availability by testing ser.in_waiting > 1,
            rather blocked the current thread with this loop since throughout
            the meantime data cannot be transceived anyway
            ''' 
            pass # wait till the chunk is delivered, otherwise the rest won't be sent

    def is_sim_locked(self):
        self.transmit('AT+CPIN?')
        txt = self.receive()
        if txt == '+CPIN: READY':
            return False
        elif txt == '+CPIN: NOT READY':
            return True
        elif txt == 'ERROR':
            raise Exception('ERROR')
        else:
            raise Exception('CPIN Inappropiate response: ' + txt)
        
    def set_pin(self, pin: str):
        if self.is_sim_locked():
            self.transmit('AT+CPIN=' + pin)
            while True:
                if self.ser.in_waiting > 1:
                    txt = self.receive()
                    if txt == 'OK':
                        break
                    elif txt == 'ERROR':
                        raise Exception('Incorrect PIN!')
                else:
                    sleep(.1) # let the other threads alive
        else:
            print('Sim already unlocked')
            
    def get_cur_operator(self):
        self.transmit('AT+COPS?')
        resp = self.receive()
        if resp.startswith('+COPS'):
            op = re.search('".*"',resp).group().strip('"')
            return op
        else:
            raise Exception('COPS Inappropiate reponse: ' + resp)

    def get_avail_operators(self):
        self.transmit('AT+COPS=?')
        resp = ''
        while True:
            if self.ser.in_waiting > 1:
                tmp = self.receive()
                if tmp.startswith('+COPS'):
                    resp = tmp
                    while not resp.endswith('OK'):
                        resp += self.receive()
                    break
            else:
                sleep(.1) # let the other threads alive
        ops_det = re.findall('\([0-9],"[^)]+","[^)]+","[^)]+"\)',resp)
        ops = []
        for op_det in ops_det:
            det = re.findall('"[^,()]+"',op_det)
            ops.append(det[0].strip('"'))
        return ops

    def is_sms_txt(self):
        self.transmit('AT+CMGF?')
        resp = self.receive()
        if resp.startswith('+CMGF'):
            x = re.search('[0-9]',resp).group()
            if x == '0':
                return False
            else:
                return True
        else:
            raise Exception('CMGF Inappropiate response: ' + resp)
        
    def set_sms_format(self, format='text'): # select text or pdu
        if format == 'text':
            self.transmit('AT+CMGF=1')
        elif format == 'pdu':
            self.transmit('AT+CMGF=0')
        else:
            raise Exception('Inexistent format type! It is either text or pdu.')
        
    def check_power_mode(self):
        self.transmit('AT+CFUN?')
        resp = self.receive()
        if resp.startswith('+CFUN:'):
            x = re.search('[0-9]',resp).group()
            if x == '1':
                print('Default functionality mode')
                return True
            else:
                if x == '0':
                    print('Minimum functionality mode')
                if x == '4':
                    print('Disabled RF transceive mode')
                return False
        else:
            raise Exception('CFUN Inappropiate response: ' + resp)
        
    def set_power_mode(self, mode='default'): # select minimal/default/disabled
        if mode == 'minimal':
            self.transmit('AT+CFUN=0')
        elif mode == 'default':
            self.transmit('AT+CFUN=1')
        elif mode == 'disabled':
            self.transmit('AT+CFUN=4')
        else:
            raise Exception('Inexistend power mode!')
        
    def get_time(self):
        self.transmit('AT+CCLK?')
        txt = self.receive()
        if txt.startswith('+CCLK'):
            date = re.findall('[0-9]{2}',txt)
            time = re.search('[0-9]{2}:[0-9]{2}:[0-9]{2}',txt).group()
            times = re.findall('[0-9]{2}',time)
            gmt = re.search('[+|-][0-9]{2}',txt).group()
            return TimeStamp(date[2],date[1],date[0],times[2],times[1],times[0],gmt)
        else:
            raise Exception('CCLK Inappropiate response: ' + txt)
        
    def get_firmware(self):
        self.transmit('AT+CGMR')
        txt = self.receive()
        if txt.startswith('Revision'):
            return txt[len('Revision:'):]
        else:
            raise Exception('CGMR Inappropiate response: ' + txt)

    def get_serial_number(self):
        self.transmit('AT+CGSN')
        return self.receive()

    def get_manufacturer(self):
        self.transmit('AT+CGMI')
        return self.receive()
    
    def get_model(self):
        self.transmit('AT+CGMM')
        return self.receive()

    def get_imsi(self):
        self.transmit('AT+CIMI')
        return self.receive()
    
    def get_iccid(self):
        self.transmit('AT+CCID')
        return self.receive()
    
    def get_gsm_reg_stat(self):
        self.transmit('AT+CREG?')
        txt = self.receive()
        if txt.startswith('+CREG'):
            x = re.findall('[0-9]',txt)
            if x[0] == '2':
                y, z = re.findall('"[0-9A-F]*"',txt)
                y = y.strip('"')
                z = z.strip('"')
                return GSMRegData(x[0],x[1],y,z)
            return GSMRegData(x[0],x[1])
        else:
            raise Exception('CREG Inappropiate response: ' + txt)
        
sim800 = SIM800L()
print(sim800.get_gsm_reg_stat())