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
                     "technology", "tech", "tender", "text", "team", "[/string,]", 
                     "O_RDWR", "__builtin_unreachable", "BLACKHOLE", "<thing>"]

    def test_default_n(self):
        result = search(self.data, "*")
        self.assertEqual(self.data, result)

    def test_max(self):
        result = search(self.data, "te*", n = "all")
        self.assertEqual(len(result), 11)
    
    def test_exact_match(self):
        result = search(["idk", "man"], "idk")
        self.assertEqual(result, ["idk"])
    
    def test_zero_results(self):
        result = search(["idk"], "man")
        self.assertEqual(result, [])
    
    def test_partial(self):
        result = search(self.data, "*re*", "2") # 4 matches in total, limited to 2
        self.assertEqual(len(result), 2)
    
    def test_null_n(self):
        result = search(self.data, "*", None)
        self.assertEqual(result, self.data[:10])

    def test_special_chars(self):
        result = search(self.data, "<*", "all")
        self.assertEqual(result, ["<thing>"])
        result = search(self.data, "*_*", "all")
        self.assertEqual(len(result), 2)
        result = search(self.data, "*,]", "all")
        self.assertEqual(result, ["[/string,]"])

if __name__ == "__main__":
    unittest.main()
