import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name == "wheel":
            self.initialize_submodules()
            self.build_mkvlib()

    def initialize_submodules(self):
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"], check=True
        )

    def build_mkvlib(self):
        script_path = Path("scripts/build_mkvlib.sh")
        if script_path.exists():
            subprocess.run([str(script_path)], check=True)
        else:
            raise FileNotFoundError(f"Build script not found: {script_path}")
