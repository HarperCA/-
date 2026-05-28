import os
import subprocess
import sys
import unittest


class ConsoleOutputTest(unittest.TestCase):
    def test_configure_console_output_prevents_gbk_unicode_crash(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "gbk:strict"

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from core.console import configure_console_output; "
                    "configure_console_output(); "
                    "print('🎲 蒙特卡洛模拟')"
                ),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode("gbk", errors="replace"))


if __name__ == "__main__":
    unittest.main()
