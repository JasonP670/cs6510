import threading


class Semaphore:
    value = 1  # need to be 1 for producer consumer
    value_lock = threading.Lock()
    condition = threading.Condition(value_lock)

    @classmethod
    def set_sem_init(cls, value):
        cls.value = value

    @classmethod
    def wait(cls):
        with cls.value_lock:
            while cls.value <= 0:
                cls.condition.wait()
            cls.value -= 1

    @classmethod
    def signal(cls):
        with cls.value_lock:
            cls.value += 1
            cls.condition.notify()
