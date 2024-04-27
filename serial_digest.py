import serial
from gotify import Gotify

gotify = Gotify(
    base_url='http://localhost:80',
    app_token='A_8APqsvE8C5Rom',
)

last_dialing_number = 0

with serial.Serial('/dev/ttyS0', baudrate=115200) as ser:
    while True:
        global call_status
        data = ser.read_until().decode()
        
        if data == 'RING\r\n':
            call_status='Ring'
            ser.write(b'AT+CLCC\r\n')
            print(call_status)
            print()
        elif data == 'NO CARRIER\r\n':
            call_status='Hang'
            print(call_status)
            print()
            gotify.create_message(
                message=call_status,
                title=last_dialing_number,
            )

        if data.startswith('+CMT'):
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

        if data.startswith('+CLCC'):
            for x in data[len('+CLCC: '):-len('\r\n')].split(','):
                if x.startswith('"') and x.endswith('"'):
                    last_dialing_number = number = x.strip('"')
                    print(number)
                    print()
                    gotify.create_message(
                        message=call_status,
                        title=number,
                    )
                    break
