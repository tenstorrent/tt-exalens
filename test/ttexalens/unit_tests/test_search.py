# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Unit test for ttexalens/util.py:search.
import unittest
from ttexalens.util import search
from fnmatch import fnmatch

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.data = ["test", "testing", "tested", "Tenstorrent", "Tensix", 
                     "status", "step", "read", "reset", "terminal emulator", 
                     "technology", "tech", "tender", "text", "team"]

    def test_default(self):
        result = search(self.data, "te*")
        self.assertEqual(len(result), 10) # 11 in total, but search is called with default n

    def test_max(self):
        result = search(self.data, "te*", n = "max")
        expected = [s for s in self.data if fnmatch(s.lower(), "te*")]
        self.assertEqual(result, expected)
    
    def test_negative(self):
        result = search(self.data, "te*", n = -1)
        self.assertEqual(len(result), 11)
    
    def test_exact(self):
        result = search(["idk", "man"], "idk")
        self.assertEqual(result, ["idk"])
    
    def test_zero_results(self):
        result = search(["idk"], "man")
        self.assertEqual(result, [])
    
    def test_partial(self):
        result = search(self.data, "*re*", "2") # 3 matches
        self.assertEqual(len(result), 2)

if __name__ == "__main__":
    unittest.main()
