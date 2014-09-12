import os
import random
import sys
import unittest
sys.path.insert(0, "..\\src")

import files.list


class SingleFileTest(unittest.TestCase):
    def test_create_blank_file(self):
        file_name = "tmp"
        file_list = files.list.FileList()
        file_list.append(file_name, 0)
        file_list.seize()
        file_list.release()
        is_file_created = os.path.isfile(file_name)
        self.assertTrue(is_file_created)
        os.remove(file_name)

    def test_create_file(self):
        file_length = 10
        file_name = "tmp"
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.seize()
        file_list.release()
        created_file_length = os.path.getsize(file_name)
        self.assertEqual(created_file_length, file_length)
        os.remove(file_name)

    def test_create_large_file(self):
        file_length = 1 << 33    # 8 GB
        file_name = "tmp"
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.seize()
        file_list.release()
        created_file_length = os.path.getsize(file_name)
        self.assertEqual(created_file_length, file_length)
        os.remove(file_name)

    def test_file_already_exists_and_has_the_same_length(self):
        file_length = 10
        file_name = "tmp"
        file_contents = "x" * file_length
        with open(file_name, "wb") as descriptor:
            descriptor.write(file_contents)
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.seize()
        file_list.release()
        with open(file_name, "rb") as descriptor:
            new_file_contents = descriptor.read(file_length)
        self.assertEqual(file_contents, new_file_contents)
        os.remove(file_name)

    def test_file_already_exists_but_smaller(self):
        file_length = 10
        file_name = "tmp"
        with open(file_name, "wb") as descriptor:
            descriptor.seek(file_length - 1 - 1)
            descriptor.write("\0")
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.seize()
        file_list.release()
        new_file_length = os.path.getsize(file_name)
        self.assertEqual(file_length, new_file_length)
        os.remove(file_name)

    def test_file_already_exists_but_larger(self):
        file_length = 10
        file_name = "tmp"
        with open(file_name, "wb") as descriptor:
            descriptor.seek(file_length - 1 + 1)
            descriptor.write("\0")
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.seize()
        file_list.release()
        new_file_length = os.path.getsize(file_name)
        self.assertEqual(file_length, new_file_length)
        os.remove(file_name)

    def test_open_existing_file(self):
        file_length = 10
        file_name = "tmp"
        file_contents = "x" * file_length
        with open(file_name, "wb") as descriptor:
            descriptor.write(file_contents)
        file_list = files.list.FileList()
        file_list.append(file_name)
        file_list.seize()
        file_list.release()
        with open(file_name, "rb") as descriptor:
            new_contents = descriptor.read()
        self.assertEqual(new_contents, file_contents)
        os.remove(file_name)


class MultiFileTest(unittest.TestCase):
    def test_create_files(self):
        files_ = [
            ("File 1", 10),
            ("File 2", 15),
            ("File 3", 20),
            ("File 4", 0),
            ("File 5", 10),
        ]
        file_list = files.list.FileList()
        for file_ in files_:
            file_list.append(*file_)
        file_list.seize()
        file_list.release()
        for file_name, file_length in files_:
            created_file_length = os.path.getsize(file_name)
            self.assertEqual(created_file_length, file_length)
            os.remove(file_name)


class IOTest(unittest.TestCase):
    def test_write_single(self):
        file_name = "tmp"
        file_length = 11
        piece_length = 8
        pieces = [
            "x" * piece_length,
            "y" * piece_length
        ]
        file_list = files.list.FileList()
        file_list.append(file_name, file_length)
        file_list.set_piece_length(piece_length)
        file_list.seize()
        for index in xrange(len(pieces)):
            file_list.write(index, pieces[index])
        file_list.release()
        with open(file_name, "rb") as descriptor:
            contents = descriptor.read()
        expected = "".join(pieces)[:file_length]
        self.assertEqual(contents, expected)
        os.remove(file_name)

    def test_read_single(self):
        file_name = "tmp"
        file_contents = "abcdefghijklmnopqrstuvwxyz" * 10
        piece_length = random.randint(1, len(file_contents) / 10)
        with open(file_name, "wb") as descriptor:
            descriptor.write(file_contents)
        file_list = files.list.FileList()
        file_list.append(file_name)
        file_list.set_piece_length(piece_length)
        file_list.seize()
        piece_index = random.randint(0, 10)
        piece = file_list.read(piece_index)
        expected = file_contents[piece_length*piece_index:piece_length*(piece_index+1)]
        self.assertEqual(piece, expected)


if __name__ == "__main__":
    unittest.main()
