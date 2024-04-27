import serial

with serial.Serial('/dev/ttyS0', baudrate=115200) as ser:
    while True:
        data = ser.read_until().decode()
        if data == 'RING\r\n':
            title='Ring'
            ser.write(b'AT+CLCC\r\n')
            print(title)
            print()
        if data == 'NO CARRIER\r\n':
            title='Hang'
            print(title)
            print()
        if data.startswith('+CMT'):
            [number,_,date,hour] = [x.strip('"') for x in data[len('+CMT: '):-len('\r\n')].split(',')]
            title='Message'
            message = ser.read_until(b'\r\n').decode()[:-2]
            print(title)
            print(number[2:])
            print(date + ' ' + hour)
            print(message)
            print()
        if data.startswith('+CLCC'):
            for x in data[len('+CLCC: '):-len('\r\n')].split(','):
                if x.startswith('"') and x.endswith('"'):
                    number = x.strip('"')
                    print(number)
                    print()
                    break