"""Focused tests for safe local desktop tool behavior."""

import tempfile
import unittest
from pathlib import Path

from system_tools import SystemTools


class SystemToolsTests(unittest.TestCase):
    """Verify read-only directory access and constrained action dispatch."""

    def setUp(self) -> None:
        """Create a tool instance for each test."""
        self.tools = SystemTools()

    def test_list_directory_returns_entry_names(self) -> None:
        """List names without exposing file contents."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            Path(temporary_directory, "notes.txt").write_text("private", encoding="utf-8")

            result = self.tools.list_directory(temporary_directory)

        self.assertEqual(result, "notes.txt")
        self.assertNotIn("private", result)

    def test_list_directory_rejects_a_file_path(self) -> None:
        """Reject a file where the tool requires a directory."""
        with tempfile.NamedTemporaryFile() as temporary_file:
            with self.assertRaises(ValueError):
                self.tools.list_directory(temporary_file.name)

    def test_application_allowlist_rejects_unknown_program(self) -> None:
        """Do not pass arbitrary application names to process creation."""
        with self.assertRaises(ValueError):
            self.tools.launch_application("powershell")

    def test_website_tool_rejects_non_http_schemes(self) -> None:
        """Reject non-web schemes before invoking the default browser."""
        with self.assertRaises(ValueError):
            self.tools.open_website("file:///C:/Windows/win.ini")

    def test_dispatch_rejects_unknown_tools(self) -> None:
        """Reject tool names not explicitly registered by the application."""
        with self.assertRaises(ValueError):
            self.tools.execute("run_shell", {"command": "whoami"})


if __name__ == "__main__":
    unittest.main()
