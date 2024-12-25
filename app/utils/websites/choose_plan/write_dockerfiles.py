import paramiko

def write_docker_files(ssh_client: paramiko.SSHClient, plan_name: str, dir_path: str, website_id: int, app_port: int, build_script: str, start_script: str) -> int:
    """Writes Dockerfile and docker-compose.yml files to the website directory indicated by ``dir_path``.
    plan_name is as saved in database ; currently supported values are:
    - "Node.js"
    - "Node.js + MySQL"
    - "Node.js + MySQL + Redis"
    Return the exposed port of Node.js.
    """
    import os
    from app.utils.ssh import execute_command, CommandExecutionError
    import random

    # Choose an empty port
    while True:
        port = random.randint(1024, 65535)
        try:
            execute_command(ssh_client, f"ss -tuln | grep -q \":{port} \"")
        except CommandExecutionError as e:
            if len(e.out.strip()) == 0 and len(e.err.strip()) == 0 and e.return_code == 1:
                break
            raise

    docker_file_content_by_lines, docker_compose_content_by_lines = render_docker_files(plan_name, website_id, app_port, port, build_script, start_script)
    dir_path = f"~/{website_id}/"
    docker_compose_path = os.path.join(dir_path, 'docker-compose.yml')
    dockerfile_path = os.path.join(dir_path, 'Dockerfile')

    commands: list[str] = [
        f"echo \"\" > {docker_compose_path}",
        f"echo \"\" > {dockerfile_path}",
    ]
    commands.extend([
        f"echo \"{line}\" | tee -a {dockerfile_path}" for line in docker_file_content_by_lines
    ])
    commands.extend([
        f"echo \"{line}\" | tee -a {docker_compose_path}" for line in docker_compose_content_by_lines
    ])

    for command in commands:
        execute_command(ssh_client, command)

    return port

def render_docker_files(plan_name: str, website_id: int, app_port: int, exposed_port: int, build_script: str, start_script: str) -> tuple[list[str], list[str]]:
    """Renders Dockerfile and docker-compose.yml files.
    plan_name is as saved in database ; currently supported values are:
    - "Node.js"
    - "Node.js + MySQL"
    - "Node.js + MySQL + Redis"

    Returns a tuple of two lists: Dockerfile content and docker-compose.yml content.
    The content is split by lines.
    """
    from shlex import quote

    docker_compose_content_by_lines: list[str]
    if plan_name == "Node.js":
        docker_compose_content_by_lines = [
            f"services:",
            f"  app:",
            f"    image: node:22",
            f"    build: .",
            f"    container_name: nodejs-app-{website_id}",
            f"    ports:",
            f"      - \"{exposed_port}:{app_port}\"",
            f"    restart: always",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:{app_port}\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"networks:",
            f"  website_network_{website_id}:",
        ]
    elif plan_name == "Node.js + MySQL":
        docker_compose_content_by_lines = [
            f"services:",
            f"  app:",
            f"    image: node:22",
            f"    build: .",
            f"    container_name: nodejs-app-{website_id}",
            f"    ports:",
            f"      - \"{exposed_port}:{app_port}\"",
            f"    restart: always",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:{app_port}\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"    depends_on:",
            f"      mysql:",
            f"        condition: service_healthy",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"  mysql:",
            f"    image: mysql:8.0",
            f"    container_name: mysql-container-{website_id}",
            f"    environment:",
            f"      MYSQL_ROOT_PASSWORD: root",
            f"      MYSQL_DATABASE: my_database",
            f"    volumes:",
            f"      - mysql_data:/var/lib/mysql",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"mysqladmin\", \"ping\", \"-h\", \"localhost\", \"-uroot\", \"-proot\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"volumes:",
            f"  mysql_data:",
            f"    driver: local",
            f"networks:",
            f"  website_network_{website_id}:",
        ]
    elif plan_name == "Node.js + MySQL + Redis":
        docker_compose_content_by_lines = [
            f"services:",
            f"  app:",
            f"    image: node:22",
            f"    build: .",
            f"    container_name: nodejs-app-{website_id}",
            f"    ports:",
            f"      - \"{exposed_port}:{app_port}\"",
            f"    restart: always",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:{app_port}\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"    depends_on:",
            f"      mysql:",
            f"        condition: service_healthy",
            f"      redis:",
            f"        condition: service_healthy",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"  mysql:",
            f"    image: mysql:8.0",
            f"    container_name: mysql-container-{website_id}",
            f"    environment:",
            f"      MYSQL_ROOT_PASSWORD: root",
            f"      MYSQL_DATABASE: my_database",
            f"    volumes:",
            f"      - mysql_data:/var/lib/mysql",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"mysqladmin\", \"ping\", \"-h\", \"localhost\", \"-uroot\", \"-proot\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"  redis:",
            f"    image: redis:alpine",
            f"    container_name: redis-container-{website_id}",
            f"    networks:",
            f"      - website_network_{website_id}",
            f"    healthcheck:",
            f"      test: [\"CMD\", \"redis-cli\", \"ping\"]",
            f"      interval: 20s",
            f"      timeout: 10s",
            f"      retries: 10",
            f"volumes:",
            f"  mysql_data:",
            f"    driver: local",
            f"networks:",
            f"  website_network_{website_id}:",
        ]
    else:
        raise ValueError(f"Unsupported plan_name: {plan_name}")
    
    start_script_in_list: list[str] = start_script.split()
    docker_file_content_by_lines: list[str] = [
        f"FROM node:22",
        f"WORKDIR /app",
        f"COPY . .",
        f"RUN {build_script}", # possible security issue here
        f"EXPOSE {app_port}",
        f"CMD [{', '.join(quote(arg) for arg in start_script_in_list)}]",
    ]

    return docker_file_content_by_lines, docker_compose_content_by_lines
