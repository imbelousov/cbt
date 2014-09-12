import random
import sys
import unittest
sys.path.insert(0, "..\\src")

import peer.buffer


class PeerBufferTest(unittest.TestCase):
    def test_push_pull(self):
        buf = peer.buffer.Buffer()
        data = [
            "01234567",
            "asdfghjk",
            "qwertyuiop"
        ]
        for line in data:
            buf.push(line)
        data = "".join(data)
        new_data = buf.pull(5)
        self.assertEqual(data[0:5], new_data)
        new_data = buf.pull(15)
        self.assertEqual(data[5:20], new_data)
        new_data = buf.pull(1000)
        self.assertEqual(data[20:], new_data)


if __name__ == "__main__":
    unittest.main()
