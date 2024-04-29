from threading import Thread, Lock
from time import sleep

mutex_lock = Lock()

def thread_1():
    print("Thread 1: Starting")
    while True:
        try:
            x = input('Mere')
            print('Thread 1: ' + x)
            mutex_lock.acquire()
            sleep(1)
        finally:
            mutex_lock.release()

def thread_2():
    print('Thread 2: Starting')
    while True:
        try:
            mutex_lock.acquire()
            print('Thread 2: ')
            sleep(1)
        finally:
            mutex_lock.release()

if __name__ == "__main__":
  thread1 = Thread(target=thread_1)
  thread2 = Thread(target=thread_2)

  thread1.start()
  thread2.start()

  thread1.join()
  thread2.join()

  print("Main thread: Done")
