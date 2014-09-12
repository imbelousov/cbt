import threading


class Buffer(object):
    def __init__(self):
        self._buf = []
        self._length = 0
        self._lock = threading.Lock()
        self._offset = 0

    def __len__(self):
        """Return total length of stored data."""
        return self._length

    def push(self, data):
        """Write <data> to the end of the buffer."""
        if not isinstance(data, str):
            raise ValueError("data: string expected")
        self._lock.acquire()
        self._buf.append(data)
        self._length += len(data)
        self._lock.release()

    def pull(self, length=None):
        """Extract the first <length> bytes from the buffer.
        If there are no so much bytes in the buffer,
        as much bytes as stored will be extracted.
        Return empty string if the buffer is empty.
        Return all the data if <length> isn't specified.

        """

        if length is None:
            # Return all the stored data
            self._lock.acquire()
            result = "".join(self._buf)
            self._buf = []
            self._length = 0
            self._offset = 0
            self._lock.release()
            return result

        if not isinstance(length, int):
            raise ValueError("length: integer expected")
        self._lock.acquire()
        if length > self._length:
            length = self._length
        result_buf = []
        result_length = 0
        while len(self._buf):
            data = self._buf[0]
            available = len(data) - self._offset
            if result_length + available > length:
                # The first string in queue has longer data than I need
                left = length - result_length
                result_buf.append(data[self._offset:self._offset+left])
                self._length -= left
                self._offset += left
                break
            else:
                # I need all the data from the first string in queue
                result_buf.append(data[self._offset:])
                self._length -= available
                self._offset = 0
                del self._buf[0]
                if result_length + available == length:
                    # All what I need is this string
                    break
                else:
                    result_length += available
        self._lock.release()
        return "".join(result_buf)
