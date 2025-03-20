import os
import platform
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
        if platform.system() == "Linux":
            script_path = Path("scripts/build_mkvlib.sh")
            subprocess.run([str(script_path)], check=True)
        elif platform.system() == "Windows":
            script_path = Path("scripts/build_mkvlib.ps1")
            subprocess.run(["powershell", "-File", str(script_path)], check=True)
        else:
            mkvlib_path = Path("mkv_merge/mkvlib/mkvlib.so")
            if not os.path.exists(mkvlib_path):
                raise RuntimeError(
                    "mkvlib.so not found. Please manually compile mkvlib.so and put it in mkv_merge/mkvlib."
                )
