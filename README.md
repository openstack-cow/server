# OpenStack Cow (Backend)

- [OpenStack Cow (Backend)](#openstack-cow-backend)
  - [Authors](#authors)
  - [Setup](#setup)
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

| #   | Student ID | Name              |
| --- | ---------- | ----------------- |
| 1   | 22028235   | Vũ Tùng Lâm       |
| 2   | 22028182   | Nguyễn Văn Thiện  |
| 3   | 22028189   | Lê Thành Đạt      |
| 4   | 22028332   | Nguyễn Phương Anh |
| 5   | 22025517   | Nguyễn Minh Châu  |
| 6   | 22028092   | Ngô Tùng Lâm      |
| 7   | 22028053   | Tạ Việt Anh       |
| 8   | 22021149   | Vi Văn Quân       |

## Setup

### Running Bare Metal

That is, you install the app as well as the required tools
straight into your own system.

#### Bare Metal: Prerequisites

- Only run on Linux!

- Python 3.12+

- MySQL Client Libraries for Python.

    On Debian/Ubuntu-based distros, run the following:

    ```sh
    sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
    ```

    For other distros, see the full guide at <https://pypi.org/project/mysqlclient/>.

- The current user (i.e. the user that installs and runs this app) must
    be in the sudoers file, so that this app could execute some critical
    commands (e.g. iptables routing) without prompting a password.

    ```sh
    echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers
    ```

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

Install pm2. Then, at the project root, run:

```sh
pm2 start ecosystem.config.js
```

It should be available at <http://localhost:5002>.

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
