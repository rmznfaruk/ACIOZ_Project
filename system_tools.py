"""Allowlisted, local operating-system actions exposed to the assistant."""

from pathlib import Path
import os
import subprocess
import webbrowser


class SystemTools:
    """Provide a small set of constrained desktop actions."""

    _APPLICATIONS = {
        "notepad": ("notepad.exe",),
        "calculator": ("calc.exe",),
        "file explorer": ("explorer.exe",),
    }

    def list_directory(self, path: str) -> str:
        """List names in an existing directory without modifying its contents."""
        directory = Path(path).expanduser().resolve()
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        entries = sorted(item.name for item in directory.iterdir())
        return "\n".join(entries[:100]) if entries else "Directory is empty."

    def open_path(self, path: str) -> str:
        """Open an existing file or directory with its registered OS handler."""
        target = Path(path).expanduser().resolve(strict=True)
        if os.name == "nt":
            os.startfile(str(target))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return f"Opened {target}"

    def launch_application(self, application: str) -> str:
        """Launch one of the explicitly allowlisted built-in applications."""
        command = self._APPLICATIONS.get(application.strip().lower())
        if command is None:
            allowed = ", ".join(sorted(self._APPLICATIONS))
            raise ValueError(f"Application is not allowlisted. Choose: {allowed}")
        subprocess.Popen(command, shell=False)
        return f"Started {application}"

    def open_website(self, url: str) -> str:
        """Open a validated HTTP or HTTPS address in the default browser."""
        from urllib.parse import urlparse

        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Only complete http:// or https:// addresses are allowed.")
        webbrowser.open(url, new=2)
        return f"Opened {url}"

    def tool_definitions(self) -> list[dict[str, object]]:
        """Return the local Ollama-compatible function schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List entries in a directory. Does not modify files.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_path",
                    "description": "Open an existing local file or directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "launch_application",
                    "description": "Start a built-in application: notepad, calculator, or file explorer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "application": {
                                "type": "string",
                                "enum": ["notepad", "calculator", "file explorer"],
                            }
                        },
                        "required": ["application"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Open an HTTP or HTTPS URL in the default browser.",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                },
            },
        ]

    def execute(self, name: str, arguments: dict[str, object]) -> str:
        """Dispatch one known tool and reject unknown functions."""
        actions = {
            "list_directory": self.list_directory,
            "open_path": self.open_path,
            "launch_application": self.launch_application,
            "open_website": self.open_website,
        }
        action = actions.get(name)
        if action is None:
            raise ValueError(f"Unknown system tool: {name}")
        return action(**arguments)  # type: ignore[arg-type]
