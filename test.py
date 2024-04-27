array1 = b'abc\r\nOK'
array2 = 'zzzz\r\nOK'
array3 = 'zzzz\nOK'
print(array1[-4:] == array2[-4:])
print(array1[-4:] == array3[-4:])
print(array1[-4:])