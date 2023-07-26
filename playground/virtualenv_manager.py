
import string
import random
import os
import subprocess
from virtualenv import cli_run


RANDOM_NAME_LENGTH = 16


class VirtualenvManager:
    def __init__(self, name: str = "", base_path="./tmp") -> None:
        if not name:
            name = ""
            for _ in range(RANDOM_NAME_LENGTH):
                population = string.ascii_letters + string.digits
                char = random.sample(population, k=1)
                name += char[0]
        self.name = name
        self.path = os.path.join(base_path, name)
        self.python_interpreter = os.path.join(self.path, "bin/python3")
        self.dependencies = []

    def add_dependency(self, dependency):
        self.dependencies.append(dependency)

    def create_env(self):
        cli_run([self.path], setup_logging=False)

    def install_dependencies(self):
        process = subprocess.run(
            [self.python_interpreter, "-m", "pip", "install"] + self.dependencies,
            capture_output=True,
        )
        return process
