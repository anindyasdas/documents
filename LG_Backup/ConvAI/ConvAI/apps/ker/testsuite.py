import unittest

#discover test case modules under "test directory
suite = unittest.TestLoader().discover("test")
#run the identified test cases
unittest.TextTestRunner(verbosity=2).run(suite)