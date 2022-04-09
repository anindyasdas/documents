import unittest
from . import info_engine_test

suite = unittest.TestLoader().loadTestsFromModule(info_engine_test)
unittest.TextTestRunner(verbosity=2).run(suite)