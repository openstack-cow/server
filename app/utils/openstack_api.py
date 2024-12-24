import openstack

_openstack_connection = None

def get_openstack_connection():
    global _openstack_connection
    try:
        _openstack_connection = openstack.connect(cloud='envvars')
        print("Successfully connect to Openstack")
    except Exception as e:
        print("NOTE THAT YOU HAVE TO source admin-openrc BEFORE RUNNING THIS APP")
        raise e

    return _openstack_connection
