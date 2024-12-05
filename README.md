# CryptoToolsLtd

- [CryptoToolsLtd](#cryptotoolsltd)
  - [Authors](#authors)
  - [Setup](#setup)
    - [Using Docker](#using-docker)
      - [Docker: Prerequisites](#docker-prerequisites)
      - [Docker: Build the Image](#docker-build-the-image)
      - [Docker: Launch the App](#docker-launch-the-app)
    - [Running Bare Metal](#running-bare-metal)
      - [Bare Metal: Prerequisites](#bare-metal-prerequisites)
      - [Bare Metal: Install Python Packages](#bare-metal-install-python-packages)
      - [Bare Metal: Create Database and Setup Environment Variables](#bare-metal-create-database-and-setup-environment-variables)
      - [Bare Metal: Launch the App](#bare-metal-launch-the-app)
  - [Advanced Use](#advanced-use)
    - [Database Migration](#database-migration)
  - [License](#license)

## Authors

We are a group of students at UET - VNU.

| #   | Student ID | Name             |
| --- | ---------- | ---------------- |
| 1   | 22028235   | Vũ Tùng Lâm      |
| 2   | 22028182   | Nguyễn Văn Thiện |
| 3   | 22028189   | Lê Thành Đạt     |
| 4   | 22028332   | Nguyễn Phương Anh|
| 5   | 22025517   | Nguyễn Minh Châu |
| 6   | 22028092   | Ngô Tùng Lâm     |
| 7   | 22028053   | Tạ Việt Anh      |
| 8   | 22021149   | Vi Văn Quân   |

## Setup

Using Docker is easier!

### Using Docker

#### Docker: Prerequisites

- Docker (tested with version 27.3.1, Ubuntu 22.04)

#### Docker: Build the Image

This step is done only once. In the project root, run:

```sh
docker compose build
```

If something fails, try adding the magic word `sudo` (Linux)
or running the command as admin (Windows).

#### Docker: Launch the App

When the previous setup steps have been done,
now whenever you need to run the app, just
enter this one command (at the project root):

```sh
docker compose up
```

### Running Bare Metal

That is, you install the required tools straight into your
own system.

#### Bare Metal: Prerequisites

- Python 3.12+

- MySQL Client Libraries for Python.

    On Debian/Ubuntu-based distros, run the following:

    ```sh
    sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
    ```

    For other distros (and other operating systems), see the full guide at <https://pypi.org/project/mysqlclient/>.

#### Bare Metal: Install Python Packages

You may want to create and activate a virtual environment
(venv) first. Then, at the project root, run

```sh
pip install -r requirements.txt
```

#### Bare Metal: Create Database and Setup Environment Variables

You have to create a `.env` file at the project root
containing the values of the required environment
variables. See the `example.env` file to know what
those variables are.

Some variables require setting up a database and
a Redis server.

After specifying the variables properly, you now
have to migrate the database. Run (after the venv
is activated):

```sh
flask db upgrade
```

#### Bare Metal: Launch the App

Activate the venv if necessary. Then, at the project
root, execute

```sh
flask run --port=8000
```

It should be available at <http://localhost:8000>.

Alternatively, to enable hot-reloading (automatically
reload the app when file changes are detected), run
the following command (still after activating venv
and at the project root):

```sh
python debug.py
```

It should also be available at <http://localhost:8000>.
You can specify a different port:

```sh
python debug.py 3000
```

## Advanced Use

### Database Migration

Whenever some models change, create a new migration
and apply it for the changes to actually take
effect/be reflected in the database.

To do that, activate the venv if necessary, then
execute

```sh
flask db migrate -m "Migration content, e.g. rename column C of table T"
flask db upgrade
```

## License

Copyright (C) 2024-now Vũ Tùng Lâm et.al.

Licensed under the 3-clause BSD license. See
[LICENSE.txt](./LICENSE.txt) for details.
