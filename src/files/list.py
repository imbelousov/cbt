import os


class FileList(object):
    def __init__(self):
        self._busy = False
        self._count = 0
        self._descriptors = []
        self._file_lengths = []
        self._file_names = []
        self._map = []
        self._piece_length = 0

    def __del__(self):
        if self._busy:
            self.release()

    def append(self, path, length=None):
        """Register file in list.
        Args:
            path: relative or absolute path to the file.
            length [optional]: size of the file. Do not
                specify it if file does already exist
                and certainly correct.

        """
        if self._busy:
            raise ValueError("File list is already busy")
        if path in self._file_names:
            raise ValueError("This file is already within the list")
        if not isinstance(path, basestring):
            raise ValueError("path: string expected")
        if length is None:
            if not os.path.isfile(path):
                raise IOError("This file does not exist. Specify <length> to create a new file.")
            length = os.path.getsize(path)
        if not isinstance(length, int):
            raise ValueError("length: integer expected")
        self._count += 1
        self._descriptors.append(None)
        self._file_lengths.append(length)
        self._file_names.append(path)
        if self._piece_length:
            self._make_map()

    def force_add_piece(self):
        self._map.append([])

    def get_files_by_piece(self, piece_index):
        if not self._piece_length:
            raise ValueError("At first determine piece length")
        if not 0 <= piece_index < self.get_piece_count():
            raise IndexError("This piece does not exist")
        files = []
        for file_index, _, _ in self._map[piece_index]:
            files.append(self._file_names[file_index])
        return files

    def get_piece_count(self):
        return len(self._map)

    def read(self, piece):
        if not self._busy:
            raise IOError("At first seize file list")
        if not 0 <= piece < self.get_piece_count():
            return None
        buf = []
        for file_index, offset, length in self._map[piece]:
            descriptor = self._descriptors[file_index]
            descriptor.seek(offset)
            data = descriptor.read(length)
            buf.append(data)
        result = "".join(buf)
        result_len = len(result)
        if result_len != self._piece_length:
            result = "".join((
                result,
                "\0" * (self._piece_length - result_len)
            ))
        return result

    def release(self):
        if not self._busy:
            return
        for index in xrange(self._count):
            descriptor = self._descriptors[index]
            if descriptor:
                descriptor.close()
                self._descriptors[index] = None
        self._busy = False

    def seize(self):
        if self._busy:
            return
        for index in xrange(self._count):
            if self._descriptors[index]:
                continue
            file_name = self._file_names[index]
            file_length = self._file_lengths[index]
            file_name = os.path.abspath(file_name)
            file_path = os.sep.join(file_name.split(os.sep)[:-1])
            if not os.path.isdir(file_path):
                os.makedirs(file_path)
            if os.path.isdir(file_name):
                raise SystemError("Remove or rename directory \"%s\"" % file_name)
            create_new_file = True
            if os.path.isfile(file_name):
                exist_file_length = os.path.getsize(file_name)
                if exist_file_length == file_length:
                    create_new_file = False
            if create_new_file:
                descriptor = open(self._file_names[index], "wb")
                if file_length > 0:
                    descriptor.seek(file_length - 1)
                    descriptor.write("\0")
                descriptor.close()
            descriptor = open(self._file_names[index], "r+b")
            self._descriptors[index] = descriptor
        self._busy = True

    def set_piece_length(self, length):
        if self._busy:
            raise ValueError("File list is already busy")
        if length <= 0:
            raise ValueError("Piece length must be greater than 0")
        self._piece_length = length
        if self._count:
            self._make_map()

    def write(self, piece, data):
        if not self._busy:
            raise IOError("At first seize file list")
        if not 0 <= piece < self.get_piece_count():
            return
        inner_offset = 0
        for file_index, offset, length in self._map[piece]:
            descriptor = self._descriptors[file_index]
            descriptor.seek(offset)
            descriptor.write(data[inner_offset:inner_offset+length])
            inner_offset += length

    def _make_map(self):
        self._map = []
        file_index = 0
        file_offset = 0
        piece_offset = 0
        piece_parts = []
        while True:
            file_length = self._file_lengths[file_index]
            file_left = file_length - file_offset
            part_length = self._piece_length - piece_offset
            piece_parts.append((file_index, file_offset, min(part_length, file_left)))
            if file_left <= part_length:
                file_index += 1
                file_offset = 0
                piece_offset += file_left
            if file_left >= part_length:
                file_offset += part_length
                piece_offset = 0
                self._map.append(piece_parts)
                piece_parts = []
            if file_left == part_length:
                file_offset = 0
            if file_index == self._count:
                if len(piece_parts):
                    self._map.append(piece_parts)
                break
