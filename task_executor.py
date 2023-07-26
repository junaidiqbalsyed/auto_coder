
from agents.planner import Planner
from agents.coder import Coder
from agents.linter import Linter
from agents.dependency_tracker import DependencyTracker
from playground.python_editor import PythonCodeEditor
import requests

ANSWER_PATTERN = r"[a-zA-Z]+"

PYLINT_SCORE_SUBSTRING = "Your code has been rated at "
NO_SAMPLING = "NO_SAMPLING"
PYLINT = "PYLINT"

DEPENDENCY_BLACKLIST = set(["random", "json"])
SUPPORTED_SAMPLING_STRATEGIES = set([PYLINT, NO_SAMPLING])


def _trim_md(code_editor):
    if code_editor.source_code:
        code_editor.source_code[0] = code_editor.source_code[0].replace(
            "```python", "")
        code_editor.source_code[-1] = code_editor.source_code[-1].replace(
            "```", "")
        code_editor.overwrite_code(code_editor.display_code())

# TODO: add validation to the config


class TaskExecutor:
    def __init__(self, code_editor: PythonCodeEditor,  LLM) -> None:

        # variables
        self.execute_code = True
        self.install_dependencies = True
        self.apply_linter = True
        self.check_package_is_in_pypi = True
        self.log_to_stdout = True
        self.coding_samples = 3
        self.code_sampling_strategy = "PYLINT"
        self.sampling_temperature_multipler = 0.1
        self.dependency_samples = 3
        self.max_coding_attempts = 10

        self.dependency_install_attempts = 10
        self.planner_temperature = 0
        self.coder_temperature = 0
        self.linter_temperature = 0.3
        self.dependency_tracker_temperature = 0.2

        # python code edittor
        self.code_editor = code_editor

        # Planner
        LLM.temperature = self.planner_temperature
        self.planner = Planner(LLM)

        # Coder
        LLM.temperature = self.coder_temperature
        self.coder = Coder(LLM)

        # Linter
        LLM.temperature = self.linter_temperature
        self.linter = Linter(LLM)

        # Dependency tracker
        LLM.temperature = self.dependency_tracker_temperature
        self.dependency_tracker = DependencyTracker(LLM)


    def execute(self, task: str):
        # Generating a coding plan
        plan = self.planner.execute_task(task=task). # planner llm
        print(f"the plan is {plan}")
        # Dependency installation
        installed_dependencies = False
        attempt = 0

        if self.execute_code and self.install_dependencies:
            while not installed_dependencies and attempt < self.dependency_install_attempts:
                dependencies = []
                for _ in range(self.dependency_samples):
                    dep = self.dependency_tracker.execute_task(
                        plan="\n".join(plan))
                    for d in dep:
                        d = d.replace("-", "").strip()
                        if " " in d:
                            d = d.split(" ")[0]

                        if self.check_package_is_in_pypi:
                            url = f'https://pypi.org/project/{d}'
                            res = requests.get(url)
                            if res.status_code != 200:
                                pass

                        if len(d) < 2 or d in DEPENDENCY_BLACKLIST:
                            continue

                        dependencies.append(d)

                if not dependencies:
                    break

                dependencies = list(set(dependencies))
                print(f"list of dependencies {dependencies}")
                for dependency in dependencies:
                    self.code_editor.add_dependency(dependency)

                self.code_editor.create_env()
                
                process = self.code_editor.install_dependencies()

                if process.returncode != 0:
                    # logger.error("Dependency install failed for: %s",
                    #              "\n".join(dependencies))
                    print(f"Failed to load dependencies! {dependencies}")
                    attempt += 1

                else:
                    installed_dependencies = True

            if attempt >= self.dependency_install_attempts:
                raise ValueError("Failed to install dependencies")

            # logger.info("Installed dependencies successfully!")
            print("Installed dependencies successfully!")

        # # Coding
        # if self.config.code_sampling_strategy == NO_SAMPLING:
        #     for i in range(self.config.max_coding_attempts):
        #         logger.info("Coding, attempt: %s", i)
        #         new_code = self.coder.execute_task(
        #             source_code=self.code_editor.display_code(), objective=task, plan="\n".join(plan)
        #         )
        #         self.code_editor.overwrite_code(new_code)
        #         _trim_md(self.code_editor)

        #         logger.info(self.code_editor.display_code())

        #         if self.config.apply_linter:
        #             logger.info("Applying linter...")
        #             (pylint_stdout, _) = lint.py_run(
        #                 self.code_editor.filename, return_std=True)
        #             pylint_stdout = pylint_stdout.getvalue()
        #             logger.info(pylint_stdout)

        #             new_code = self.linter.execute_task(
        #                 source_code=self.code_editor.display_code(),
        #                 stdout=pylint_stdout,
        #             )
        #             logger.warn("Linted code: %s", new_code)
        #             if new_code:
        #                 self.code_editor.overwrite_code(new_code)

        #         if not self.config.execute_code:
        #             return self.code_editor.display_code()

        #         result = self.code_editor.run_code()

        #         if "Succeeded" in result:
        #             break

        # elif self.config.code_sampling_strategy == PYLINT:
        #     coding_samples = []
        #     for i in range(self.config.coding_samples):
        #         self.coder.llm.set_parameter(
        #             "temperature", i * self.config.sampling_temperature_multipler)
        #         self.planner.llm.set_parameter(
        #             "temperature", i * self.config.sampling_temperature_multipler)
        #         plan = self.planner.execute_task(task=task)
        #         logger.info(type(plan))
        #         logger.info("Parsed plan: %s", plan)

        #         logger.info("Coding sample: %s (temperature: %s)",
        #                     i, self.coder.llm.parameters["temperature"])
        #         new_code = self.coder.execute_task(
        #             source_code=self.code_editor.display_code(), objective=task, plan="\n".join(plan)
        #         )
        #         self.code_editor.overwrite_code(new_code)
        #         _trim_md(self.code_editor)

        #         logger.info(self.code_editor.display_code())
        #         logger.info("Applying linter...")

        #         (pylint_stdout, _) = lint.py_run(
        #             self.code_editor.filename, return_std=True)
        #         pylint_stdout = pylint_stdout.getvalue()
        #         pylint_lines = pylint_stdout.splitlines()
        #         linting_score_str = None
        #         for line in pylint_lines:
        #             if PYLINT_SCORE_SUBSTRING in line:
        #                 split_1 = line.split(PYLINT_SCORE_SUBSTRING)[1]
        #                 linting_score_str = split_1.split("/")[0]
        #         if not linting_score_str:
        #             logger.warn(
        #                 f"Failed to parse pylint score from stdout: {pylint_stdout}")
        #             score = -1  # Code probably does not compile
        #         else:
        #             score = float(linting_score_str)

        #         coding_samples.append({"code":  new_code, "score": score})
        #         logger.info("Sample score: %s", score)

        #     coding_samples.sort(key=lambda x: x["score"], reverse=True)
        #     highest_score = coding_samples[0]
        #     logger.info("Score of highest sample: %s", highest_score["score"])
        #     self.code_editor.overwrite_code(highest_score["code"])
        #     if not self.config.execute_code:
        #         return self.code_editor.display_code()

        #     result = self.code_editor.run_code()

        # else:
        #     raise ValueError("Invalid Sampling Strategy")

        # logger.info("Finished generating code!")

        # if "Succeeded" in result:
        #     logger.info("Source code is functional!")
        #     return "Task Success: " + result
        # else:
        #     logger.info("Failed to generate an executable source code.")
        #     return "Task Failed: " + result
