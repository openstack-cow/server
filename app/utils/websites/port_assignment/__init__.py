def assign_public_port(internal_ip_address: str, internal_port: int) -> int:
    public_port = _find_available_public_port()
    try:
        _iptables_forward(True, public_port, internal_ip_address, internal_port)
    except Exception as e:
        try:
            _iptables_forward(False, public_port, internal_ip_address, internal_port)
        except:
            pass
        raise e
    return public_port

def unassign_public_port(public_port: int, internal_ip_address: str, internal_port: int) -> None:
    _iptables_forward(False, public_port, internal_ip_address, internal_port)

def _find_available_public_port() -> int:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def _iptables_forward(enable: bool, public_port: int, internal_ip_address: str, internal_port: int) -> None:
    from app.utils.shell import execute_shell_command
    execute_shell_command(f"sudo iptables -t nat -{'A' if enable else 'D'} PREROUTING -p tcp --dport {public_port} -j DNAT --to-destination {internal_ip_address}:{internal_port}")
    # execute_shell_command(f"sudo iptables -{'A' if enable else 'D'} FORWARD -p tcp -d {internal_ip_address} --dport {internal_port} -j ACCEPT")
