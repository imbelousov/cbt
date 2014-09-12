class BasePeer(object):
    def __init__(self, ip, port):
        if not isinstance(ip, basestring):
            raise ValueError("ip: string expected")
        if not isinstance(port, int):
            raise ValueError("port: integer expected")
        self.ip = ip
        self.port = port

    def connect(self):
        """Make a connection with the peer.
        Takes and returns nothing.

        """
        pass

    def close(self):
        """Close the connection with the peer.
        Takes and returns nothing.

        """
        pass

    def poll(self):
        """Call this in the main loop.
        Takes and returns nothing.

        """
        pass

    def read(self):
        """Read downloaded data.
        Returns list of tuples: (<piece index>, <offset>, <data>).
        If there is no downloaded data, it returns an empty list.
        Takes nothing.

        """
        pass

    def request(self, piece, offset, length):
        """Request to download a new block of piece.
        Takes:
            piece: index of the piece.
            offset: offset within the piece.
            length: size of the needed block.

        """
        pass
