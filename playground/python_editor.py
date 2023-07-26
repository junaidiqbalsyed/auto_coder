import logging
from playground.base import CodeEditorTooling
from playground.virtualenv_manager import VirtualenvManager


class PythonCodeEditor(CodeEditorTooling):

    def __init__(self, filename="persistent_source.py") -> None:
        super().__init__(filename, interpreter="python3")
        self.venv = VirtualenvManager()

    def add_dependency(self, dependency):
        self.venv.add_dependency(dependency)

    def create_env(self):
        self.venv.create_env()
        self.interpreter = self.venv.python_interpreter
        

    def install_dependencies(self):
        process = self.venv.install_dependencies()
        return process
