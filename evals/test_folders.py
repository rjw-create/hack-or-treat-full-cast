"""Tests for evals.folders and the three commands run with no folder. Run: python -m unittest discover -s evals -t ."""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.placeholders import DEFAULT_FIXTURE, generate
from evals import audio_checks, coverage, credits, folders


class DefaultFolder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.placeholder = generate(DEFAULT_FIXTURE, Path(cls.tmp.name) / "placeholder")
        cls.missing = Path(cls.tmp.name) / "missing"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("FULLCAST_OUTPUT_DIR", None)

    def use(self, real, placeholder):
        for name, value in (("output_dir", lambda: real), ("PLACEHOLDER_DIR", placeholder)):
            patcher = mock.patch.object(folders, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_quietly(self, main):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = main([])
        return code, err.getvalue()

    def test_shared_folder_present_is_used_without_a_message(self):
        self.use(real=self.placeholder, placeholder=self.missing)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(folders.default_folder(), (self.placeholder, False))
        self.assertEqual(err.getvalue(), "")

    def test_shared_folder_missing_falls_back_to_placeholder(self):
        self.use(real=self.missing, placeholder=self.placeholder)
        code, err = self.run_quietly(coverage.main)
        self.assertEqual(code, 0)
        self.assertIn("using the placeholder output", err)
        self.assertEqual(err.count("\n"), 1)

    def test_credits_fallback_reads_placeholder_rows_as_sample(self):
        self.use(real=self.missing, placeholder=self.placeholder)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(credits.main([]), 0)
        self.assertIn("SAMPLE DATA", out.getvalue())

    def test_both_missing_says_to_run_the_placeholder_steps(self):
        self.use(real=self.missing, placeholder=self.missing / "placeholder")
        for main in (coverage.main, audio_checks.main, credits.main):
            code, err = self.run_quietly(main)
            self.assertEqual(code, 1)
            self.assertIn("Run the placeholder steps", err)

    def test_folder_set_by_env_var_is_never_swapped(self):
        os.environ["FULLCAST_OUTPUT_DIR"] = str(self.missing)
        self.use(real=self.missing, placeholder=self.placeholder)
        self.assertEqual(folders.default_folder(), (self.missing, False))


if __name__ == "__main__":
    unittest.main()
