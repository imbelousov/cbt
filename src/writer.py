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
        while len(data):
            f = self._get_file(offset)
            if not f:
                break
            offset_inside = offset - f.offset
            border = f.size - offset_inside
            if border > len(data):
                border = len(data)
            this_file_data = data[:border]
            self._write_to_file(f, offset_inside, this_file_data)
            data = data[border:]
            offset += border

    def _get_file(self, offset):
        for f in self.files:
            if f.offset <= offset < f.offset + f.size:
                return f
        return None

    def _write_to_file(self, f, offset, data):
        with open(f.name, "r+b") as fd:
            fd.seek(offset)
            fd.write(data)
