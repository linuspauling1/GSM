from threading import Thread, Lock
from time import sleep

mutex_lock = Lock()

def thread_1():
    print("Thread 1: Starting")
    for i in range(50):
        try:
            mutex_lock.acquire()
            print('Thread 1: ' + str(i))
        finally:
            mutex_lock.release()

def thread_2():
    print('Thread 2: Starting')
    for i in range(50):
        try:
            mutex_lock.acquire()
            print('Thread 2: ' + str(i))
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
