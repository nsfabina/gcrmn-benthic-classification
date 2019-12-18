import logging
import shlex
import subprocess


def run_command_line(command: str, logger: logging.Logger = None, assert_success: bool = True) \
        -> subprocess.CompletedProcess:
    completed = subprocess.run(shlex.split(command), capture_output=True)
    if completed.stderr:
        message = 'command:  {}\n\nstdout:  {}\n\nstderr:  {}'.format(
            command, completed.stdout.decode('utf-8'), completed.stderr.decode('utf-8'))
        if logger:
            logger.error(message)
    if assert_success:
        assert completed.returncode == 0, message
    return completed
