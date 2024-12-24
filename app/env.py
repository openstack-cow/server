from dotenv import load_dotenv
load_dotenv()

import os
from urllib.parse import quote

# print(os.environ)
def readNonEmptyStringEnv(key: str) -> str:
    value = os.environ.get(key, None)
    if value is None or len(value) == 0:
        raise RuntimeError(f"Environment variable {key} is invalid or missing")
    return value

def readUriComponentEnv(key: str) -> str:
    value = readNonEmptyStringEnv(key)
    return quote(value)

def readIntEnv(key: str) -> int:
    value = readNonEmptyStringEnv(key)
    return int(value)

#############################################
# Environment variables should be consumed by
# importing the following variables, not by
# reading os.environ directly.
#############################################

FLASK_ENV = readNonEmptyStringEnv("FLASK_ENV")

SECRET_KEY = readNonEmptyStringEnv("SECRET_KEY")

MYSQL_HOSTNAME = readUriComponentEnv("MYSQL_HOSTNAME")
MYSQL_HOSTPORT = readIntEnv("MYSQL_HOSTPORT")
MYSQL_USERNAME = readNonEmptyStringEnv("MYSQL_USERNAME")
MYSQL_PASSWORD = readNonEmptyStringEnv("MYSQL_PASSWORD")
MYSQL_DATABASE = readNonEmptyStringEnv("MYSQL_DATABASE")
NOVA_VM_FLAVOR_ID=readNonEmptyStringEnv("NOVA_VM_FLAVOR_ID")
NOVA_VM_IMAGE_ID=readNonEmptyStringEnv("NOVA_VM_IMAGE_ID")
NOVA_VM_NETWORK_ID=readNonEmptyStringEnv("NOVA_VM_NETWORK_ID")
NOVA_VM_EXTERNAL_NETWORK_ID=readNonEmptyStringEnv("NOVA_VM_EXTERNAL_NETWORK_ID")
NOVA_VM_SECURITY_GROUP_ID=readNonEmptyStringEnv("NOVA_VM_SECURITY_GROUP_ID")
NOVA_VM_KEYPAIR_NAME=readNonEmptyStringEnv("NOVA_VM_KEYPAIR_NAME")
NOVA_VM_PRIVATE_KEY_PATH=readNonEmptyStringEnv("NOVA_VM_PRIVATE_KEY_PATH")

