import threading
from collections import deque

buffer = deque()
buffer_lock = threading.Lock()

def push(data):
    with buffer_lock:
        buffer.append(data)

def pop_all():
    with buffer_lock:
        items = list(buffer)
        buffer.clear()
    return items
