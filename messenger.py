import serial
from time import sleep

wait = '1' # wait for ... sec
pin = '0000'
number = '0744604883'
text = 'textul 2'
ctrlZ = chr(26)

gsm = {'check':'AT',
       'wait':'WAIT=' + wait,
       'sig_quality':'AT+CSQ',
       'ready':'AT+CPIN?',
       'pin':'AT+CPIN=' + pin,
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
       'send_sms':
        'AT+CMGS=' + '"' + number + '"' + '\n' + text + ctrlZ,
       'list_sms':'AT+CMGL="ALL"',
       'dial':'ATD' + number + ';',
       'dial_last':'ATDL',
       'hangup':'ATH',
       'find_number':'AT+CNUM',
       'answer':'ATA',
       'auto_answer':'ATS0=',#1 yes, 0 no
       }

def transceive(message):
    with serial.Serial('/dev/ttyS0', baudrate=115200, timeout=3) as ser:
        message = gsm[message] + '\n'
        ser.write(message.encode())
        response = b''
        while True:
            data = ser.read(1)
            if data:
                response += data
                if response[-4:] == b'\r\nOK':
                    break
                elif response[-7:] == b'\r\nERROR':
                    break
        print(response.decode())
        ser.close()

transceive('check_sms')
transceive('send_sms')
transceive('dial')
sleep(5)
transceive('hangup')