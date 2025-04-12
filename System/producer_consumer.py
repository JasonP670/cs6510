from .semaphore import Semaphore
from typing import List


class Producer:
    @classmethod
    def produce(
        cls,
        number: int,
        memory_buffer: List[int],
    ):
        # Get the lock for mutual exclusion
        Semaphore.wait()
        Logger.log_verbose(f"Producing {number}", 'GREEN')
        memory_buffer.append(number)
        # Release the lock
        Semaphore.signal()


class Consumer:
    @classmethod
    def consume(
        cls,
        number: int,
        memory_buffer: List[int]
    ):
        # Get the lock for mutual exclusion
        Semaphore.wait()
        if len(memory_buffer) > 0:
            number = memory_buffer.pop(0)
        else:
        # Release the lock
        Semaphore.signal()
