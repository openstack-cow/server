import subprocess

def execute_shell_command(command: str, raise_on_nonzero_exit_code: bool = True) -> tuple[str, str, int]:
    """
    Execute a shell command and return the output, error, and exit code.
    If raise_on_nonzero_exit_code is True, raise a subprocess.CalledProcessError exception if the exit code is non-zero.
    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode().strip()
    err = err.decode().strip()
    exit_code = p.returncode
    if raise_on_nonzero_exit_code and exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, command, output=out, stderr=err)
    
    return out, err, exit_code
