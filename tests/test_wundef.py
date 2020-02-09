"""Test -Wundef, -Werror=undef, and -Werror flags"""
from __future__ import absolute_import, print_function

import io
import os
import sys
import tempfile
import unittest

from pcpp.pcmd import CmdPreprocessor

try:
    # python >= 3.5
    from contextlib import redirect_stderr
except ImportError:
    # python 2.7
    from contextlib import contextmanager

    @contextmanager
    def redirect_stderr(f):
        """Poor man's redirect_stderr"""
        try:
            sys.stderr, stderr = f, sys.stderr
            yield None
        finally:
            sys.stderr = stderr


class WarnErrorUndefined(unittest.TestCase):

    # bytes for NamedTemporaryFile
    TEST_DATA = b"""#if FOO == 0
int a;
#endif
"""

    # printf "#if FOO == 0\nint a;\n#endif"|cpp -Wundef
    # <stdin>:1:5: warning: "FOO" is not defined, evaluates to 0 [-Wundef]
    WARN_MESSAGE = 'warning: "FOO" is not defined, evaluates to 0 [-Wundef]'

    # printf "#if FOO == 0\nint a;\n#endif"|cpp -Werror=undef
    # <stdin>:1:5: error: "FOO" is not defined, evaluates to 0 [-Werror=undef]
    ERROR_MESSAGE = 'error: "FOO" is not defined, evaluates to 0 [-Werror=undef]'

    def run_test_case(self, args):
        """Run test case with given args
        Returns return_code, and stderr as string"""

        infile = tempfile.NamedTemporaryFile(delete=False)
        try:
            infile.write(self.TEST_DATA)
            infile.close()

            if sys.version_info[0] < 3:
                stderr = io.BytesIO()
            else:
                stderr = io.StringIO()

            with redirect_stderr(stderr):
                pcmd = CmdPreprocessor(["pcpp"] + args + [infile.name])

            return pcmd.return_code, stderr.getvalue()

        finally:
            os.remove(infile.name)

    def test_Wundef(self):
        """Warn when undefined macro with -Wundef given"""
        return_code, stderr = self.run_test_case(["-Wundef"])
        self.assertEqual(return_code, 0)
        self.assertIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)

    def test_Wundef_Wno_undef(self):
        """Don't warn with '-Wundef -Wno-undef' arg sequence macro given"""

        return_code, stderr = self.run_test_case(["-Wundef", "-Wno-undef"])
        self.assertEqual(return_code, 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)

    def test_Wno_undef_Wundef(self):
        """Warn when undefined macro with -Wno-undef -Wundef given"""

        return_code, stderr = self.run_test_case(["-Wno-undef", "-Wundef"])
        self.assertEqual(return_code, 0)
        self.assertIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)

    def test_Werror_undef(self):
        """Error when undefined macro with -Werror=undef given"""

        return_code, stderr = self.run_test_case(["-Werror=undef"])
        self.assertTrue(return_code != 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertIn(self.ERROR_MESSAGE, stderr)

    def test_Werror_undef_Wundef(self):
        """Error when undefined macro with -Werror-undef -Wundef given"""

        return_code, stderr = self.run_test_case(["-Werror=undef", "-Wundef"])
        self.assertTrue(return_code != 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertIn(self.ERROR_MESSAGE, stderr)

    def test_Werror_undef_Wno_error_undef(self):
        """No error when undefined macro with -Werror=undef -Wno-error=undef given"""

        return_code, stderr = self.run_test_case(["-Werror=undef", "-Wno-error=undef"])
        self.assertEqual(return_code, 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)

    def test_Wnoerror_undef_Werror_undef(self):
        """Error when undefined macro with -Wno-error=undef -Werror=undef given"""

        return_code, stderr = self.run_test_case(["-Wno-error=undef", "-Werror=undef"])
        self.assertTrue(return_code > 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertIn(self.ERROR_MESSAGE, stderr)

    def test_Wundef_Werror(self):
        """Error when undefined macro with -Wundef -Werror given"""

        return_code, stderr = self.run_test_case(["-Wundef", "-Werror"])
        self.assertTrue(return_code > 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertIn(self.ERROR_MESSAGE, stderr)

    def test_Werror(self):
        """No error or warning with only -Werror"""

        return_code, stderr = self.run_test_case(["-Werror"])
        self.assertEqual(return_code, 0)
        self.assertNotIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)

    def test_Wno_undef_error_overrides_Werror(self):
        """Warning with -Wno-error=undef -Werror -Wundef"""

        return_code, stderr = self.run_test_case(
            ["-Wno-error=undef", "-Werror", "-Wundef"]
        )
        self.assertEqual(return_code, 0)
        self.assertIn(self.WARN_MESSAGE, stderr)
        self.assertNotIn(self.ERROR_MESSAGE, stderr)


class NowarnDefininitionTest(unittest.TestCase):

    # bytes for NamedTemporaryFile
    TEST_DATA = b"""#if defined(FOO) && FOO == 0
int a;
#endif
"""

    def run_test_case(self, args):
        """Run test case with given args
        Returns return_code, and stderr as string"""

        infile = tempfile.NamedTemporaryFile(delete=False)
        try:
            infile.write(self.TEST_DATA)
            infile.close()

            if sys.version_info[0] < 3:
                stderr = io.BytesIO()
            else:
                stderr = io.StringIO()

            with redirect_stderr(stderr):
                pcmd = CmdPreprocessor(["pcpp"] + args + [infile.name])

            return pcmd.return_code, stderr.getvalue()

        finally:
            os.remove(infile.name)

    def test_Wundef(self):
        """Don't warn on defined(UNDEF_MACRO) and -Wundef given"""
        return_code, stderr = self.run_test_case(["-Wundef"])
        print(stderr)
        self.assertEqual(return_code, 0)
        self.assertNotIn('warning:', stderr)
        self.assertNotIn('error:', stderr)


if __name__ == "__main__":
    unittest.main()
