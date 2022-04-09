from components.info_extraction import constants
import unittest
from test import info_engine_test

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(info_engine_test)
    unittest.TextTestRunner(verbosity=2).run(suite)