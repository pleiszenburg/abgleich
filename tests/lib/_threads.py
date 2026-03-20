from threading import Thread
from typing import Callable, Dict

from typeguard import typechecked


@typechecked
class _ThreadWrapper:
    """
    wraps around thread and its kill func
    """

    def __init__(self, thread: Thread, killfunc: Callable):
        """
        constructor
        """

        self._thread = thread
        self._killfunc = killfunc

    def kill(self):
        """
        kill thread
        """

        self._killfunc()
        self._thread.join()


@typechecked
class _Threads:
    """
    manages threads so they can be killed if there is a crash
    """

    def __init__(self):
        """
        constructor
        """

        self._threads: Dict[int, _ThreadWrapper] = {}

    def clear(self):
        """
        kill dangling threads
        """

        for thread in self._threads.values():
            thread.kill()

    def register(self, thread: Thread, killfunc: Callable) -> int:
        """
        register running thread
        """

        if len(self._threads) > 0:
            idx = max(self._threads.keys()) + 1
        else:
            idx = 0
        self._threads[idx] = _ThreadWrapper(thread = thread, killfunc = killfunc)
        return idx

    def unregister(self, idx: int):
        """
        rm from register
        """

        self._threads.pop(idx)


threads = _Threads()
