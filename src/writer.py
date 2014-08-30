import file


class Writer(object):
    def __init__(self):
        self.files = []

    def append_file(self, f):
        assert isinstance(f, file.File)
        self.files.append(f)

    def create_files(self):
        for f in self.files:
            f.create()

    def write(self, offset, data):
        print "WRITE", offset, len(data)
