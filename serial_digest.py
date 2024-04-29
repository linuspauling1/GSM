import serial
from gotify import Gotify

def serial_digest():
    last_dialing_number = 0

    gotify = Gotify(
            base_url='http://localhost:80',
            app_token='A_8APqsvE8C5Rom',
    )
    
    with serial.Serial('/dev/ttyS0', baudrate=115200) as ser:
        while True:
            global call_status
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
                            break
                gotify.create_message(
                    message=call_status,
                    title=last_dialing_number,
                )
                print(last_dialing_number)
                print(call_status)
                print()
            elif data == 'NO CARRIER\r\n':
                call_status='Hang'
                gotify.create_message(
                    message=call_status,
                    title=last_dialing_number,
                )
                print(last_dialing_number)
                print(call_status)
                print()
            elif data.startswith('+CMT'):
                [number,_,date,hour] = [x.strip('"') for x in data[len('+CMT: '):-len('\r\n')].split(',')]
                message = ser.read_until(b'\r\n').decode()[:-2]
                message += '\n' + date + ' ' + hour
                title = number[2:]
                print(title)
                print(message)
                print()
                gotify.create_message(
                    message=message,
                    title=title,
                )

serial_digest()