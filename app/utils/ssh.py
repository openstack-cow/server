from app.env import NOVA_VM_PRIVATE_KEY_PATH
import paramiko
import os

def create_ssh_client_to_nova_vm(floating_ip: str):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.Ed25519Key.from_private_key_file(os.path.expanduser(NOVA_VM_PRIVATE_KEY_PATH))
    ssh_client.connect(floating_ip, port=22, username="ubuntu", pkey=private_key, timeout=120)
    print(f"Connected to the server at {floating_ip}")
    return ssh_client

class CommandExecutionError(Exception):
    """Exception raised for errors in the remote command execution."""
    def __init__(self, command: str, return_code: int, out: str, err: str):
        self.command = command
        self.return_code = return_code
        self.out = out
        self.err = err
        super().__init__(f"Command '{command}' failed with return code {return_code}. Error: {self.err.strip()}. Output: {self.out.strip()}")

def execute_command(ssh_client: paramiko.SSHClient, command: str) -> tuple[str, str]:
    _stdin, stdout, stderr = ssh_client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()  # Waits for the command to complete and gets the exit status
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if exit_status != 0:
        raise CommandExecutionError(command, exit_status, out, err)
    print(f"Command '{command}' executed successfully - stdout: {out}")
    print(f"Command '{command}' executed successfully - stderr: {err}")
    return out, err

def quick_shell_to_nova_vm(floating_ip: str, cmd: str):
    """
    Execute a single shell command on the Nova VM instance containing the website.
    """

    ssh_client = create_ssh_client_to_nova_vm(floating_ip)
    try:
        print(f"Executing command on the Nova VM at {floating_ip}: {cmd}")
        execute_command(ssh_client, cmd)
    finally:
        ssh_client.close()
        print("Connection closed")
