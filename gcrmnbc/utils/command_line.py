import logging
import shlex
import subprocess


def run_command_line(command: str, logger: logging.Logger = None) -> None:
    completed = subprocess.run(shlex.split(command), capture_output=True)
    if completed.stderr:
        message = 'gdal command:  {}\n\ngdal stdout:  {}\n\ngdal stderr:  {}'.format(
            command, completed.stdout.decode('utf-8'), completed.stderr.decode('utf-8'))
        if logger:
            logger.error(message)
    assert completed.returncode == 0, message
    return completed
