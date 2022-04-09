import unittest

#discover test case modules under "test directory
suite = unittest.TestLoader().discover("components/test")
#run the identified test cases
unittest.TextTestRunner(verbosity=2).run(suite)