import os
import sys

import unittest

import schecker

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


class TestStringMethods(unittest.TestCase):


    def test_return_code_true(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
