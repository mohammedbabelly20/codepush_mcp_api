import os
import subprocess
from pathlib import Path


class MCPServer:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.repo_url = "https://github.com/mohammedbabelly20/codepush_mcp"
        self.repo_name = "codepush_mcp"
        self.repo_path = self.base_dir / self.repo_name

    def _run_command(self, command: list, cwd: Path = None, check: bool = True):
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.base_dir,
                check=check,
                capture_output=True,
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            if e.stderr:
                print(f"Error output: {e.stderr}")
            raise

    def _check_prerequisites(self):
        try:
            self._run_command(["git", "--version"])
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Git is not installed. Please install git first.")
            return False

        try:
            self._run_command(["uv", "--version"])
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ uv is not installed. Please install uv first.")
            print("You can install uv with: pip install uv")
            return False

        return True

    def _clone_repository(self):
        if self.repo_path.exists():
            self._run_command(["git", "pull"], cwd=self.repo_path)
            return True

        self._run_command(["git", "clone", self.repo_url], cwd=self.base_dir)
        return True

    def _setup_environment(self):
        self._run_command(["uv", "venv"], cwd=self.repo_path)
        self._run_command(["uv", "sync"], cwd=self.repo_path)

    def setup(self):
        if not self._check_prerequisites():
            return False

        if not self._clone_repository():
            return False

        try:
            self._setup_environment()
        except Exception as e:
            print(f"Error during environment setup: {e}")
            return False

        print(f"✓ MCP server setup complete at {self.repo_path}")
        return True

    def get_connection_info(self, codepush_access_key: str):
        return {
            "command": "uv",
            "args": [
                "--project",
                str(self.repo_path),
                "run",
                str(self.repo_path / "src" / "codepush_mcp" / "main.py"),
            ],
            "env": {"CODEPUSH_ACCESS_KEY": codepush_access_key},
        }
