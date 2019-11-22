import logging
import shlex
import subprocess


def run_command_line(command: str, logger: logging.Logger = None) -> None:
    completed = subprocess.run(shlex.split(command), capture_output=True)
    if completed.stderr:
        if logger:
            logger.error('gdal command:  {}'.format(command))
            logger.error('gdal stdout:  {}'.format(completed.stdout.decode('utf-8')))
            logger.error('gdal stderr:  {}'.format(completed.stderr.decode('utf-8')))
    assert completed.returncode == 0, 'See above log lines for unknown error in gdal command:  {}'.format(command)
