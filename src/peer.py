import socket
import threading
import time

import convert
import node

__all__ = ["Peer"]


class Peer(object):
    """This class implements asynchronous exchange with all peers
    in current BitTorrent network. It provides API for sending and
    receiving messages only and doesn't implement handling of messages.

    Attributes:

        nodes:
            A list of all connected, active peers (nodes). Each peer is node.Node object.

        handles:
            A dict that contains user event handlers.

    Events:

        on_recv:
            A single regular BitTorrent message is received.
            Prototype: on_recv(node, buffer).
            Where node - what peer sent this message; buffer - whole message.
            To add a handler use: peer.on_recv(function).

        on_recv_handshake:
            A handshake message is received.
            Prototype: on_recv(node, buffer).
            Args are the same with on_recv.
            To add a handler use: peer.on_recv_handshake(function).

    Methods:

        append_node(ip, port):
            Add a peer to peers list before connection.

        connect_all():
            Connect to all peers in the list.

        message():
            You have to call this method in a loop.

    """
    PROTOCOL = "BitTorrent protocol"

    def __init__(self):
        self.nodes = []
        self.handlers = {
            "on_recv": [],
            "on_recv_handshake": []
        }

    def on_recv(self, func):
        """Add on_recv handler."""
        if func not in self.handlers["on_recv"]:
            self.handlers["on_recv"].append(func)

    def on_recv_handshake(self, func):
        """Add on_recv_handshake handler."""
        if func not in self.handlers["on_recv_handshake"]:
            self.handlers["on_recv_handshake"].append(func)

    def append_node(self, ip, port):
        """Add a peer to peers list before connection."""
        for n in self.nodes:
            if (n.ip, n.port) == (ip, port):
                return
        new_node = node.Node(ip, port)
        self.nodes.append(new_node)

    def connect_all(self):
        """Connect to all peers in the list.
        Due to the fact that socket.connect() method is blocking
        connections are established in separate threads.

        """
        def connect(n):
            try:
                n.connect()
            except (socket.timeout, socket.error):
                n.close()
        threads = []
        for n in self.nodes:
            thread = threading.Thread(target=connect, args=(n,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def message(self):
        """You have to call this method in a loop.
        If there is nothing to do this method makes
        the main thread to sleep for a some time
        to reduce the load on the processor.

        """
        r = range(len(self.nodes))
        r.reverse()
        for i in r:
            if not self.nodes[i].conn:
                del self.nodes[i]
        is_buffers_empty = True
        for n in self.nodes:
            self._message_recv(n)
            self._message_send(n)
            if n.inbox.length or len(n.outbox):
                is_buffers_empty = False
        if is_buffers_empty:
            time.sleep(0.5)

    def _message_recv(self, n):
        """Try to receive a single message from the peer
        and handle it. If the message is not accepted wholly
        this method will wait.

        """
        chunk = ""
        try:
            chunk = n.conn.recv(node.Node.MAX_PART_SIZE)
        except socket.error as err:
            if err.errno != 10035:
                n.close()
        if chunk:
            n.inbox.append(chunk)
            n.last_recv = time.time()
        # Check if I need to process a buffer
        if n.inbox.length and n.inbox.length != n.inbox.bad_length:

            # Make string from buffer
            buf = "".join(n.inbox.buf)

            # Check if a handshake
            pstr_len = ord(buf[0])
            if pstr_len == len(Peer.PROTOCOL):
                # It's a handshake (or extremely huge message (about 318 MB), don't care for it)
                if len(buf) < pstr_len + 49:
                    # A handshake is not received completely
                    n.inbox.bad()
                    return
                # Call handshake handlers
                handshake = buf[0:pstr_len+49]
                for func in self.handlers["on_recv_handshake"]:
                    func(n, handshake)
                # Clear a buffer and append remaining data if they are
                n.inbox.clear()
                if len(handshake) < len(buf):
                    n.inbox.append(buf[len(handshake):])
                return

            # Other messages
            if len(buf) < 4:
                # A message is not received completely
                n.inbox.bad()
                return
            m_len = convert.uint_ord(buf[0:4])
            if len(buf) < 4 + m_len:
                # A message is not received completely
                n.inbox.bad()
                return
            # Call other messages handlers
            m_buf = buf[0:4+m_len]
            for func in self.handlers["on_recv"]:
                func(n, m_buf)
            # Clear a buffer and append remaining data if they are
            n.inbox.clear()
            if len(m_buf) < len(buf):
                n.inbox.append(buf[len(m_buf):])

    def _message_send(self, n):
        """Try to send the first message in the queue.
        If the last message was sent a long enough
        send a keep-alive message.
        Supports "delayed sending" - sending the next
        message after a certain time. Just send a number
        to peer to wait n seconds.

        """
        try:
            outbox_len = len(n.outbox)
            elapsed = time.time() - n.last_send
            if not outbox_len and elapsed > 100:
                # Keep-alive message
                n.conn.send(convert.uint_chr(0))
                n.last_send = time.time()
            for x in xrange(outbox_len):
                chunk = n.outbox[0]
                if type(chunk) is int:
                    # "Sleep" message
                    timestamp = chunk
                    if time.time() > timestamp:
                        del n.outbox[0]
                    return
                n.conn.send(chunk)
                n.last_send = time.time()
                del n.outbox[0]
            n.outbox = []
        except socket.error:
            n.close()
