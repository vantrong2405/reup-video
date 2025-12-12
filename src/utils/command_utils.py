import subprocess
import sys

class CommandUtils:
    @staticmethod
    def run_command(command, check=True):
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and result.returncode != 0:
            print(f"Command failed with output:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        return result
