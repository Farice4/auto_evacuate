FILE = '/.eayunstack/node-list'

def ipaddr_get():
    """Use node-list get idrac ip address

    :return: [{'nodename':'node-15', 'role': 'compute', 'ip':'192.168.1.242']}
    """
    ip = []
    with open(FILE) as f:
        for i in f.readlines():
            if 'compute' in i:
                s = i.split('\n')[0]
                n = s.split(':')
                ip.append({'nodename':n[1], 'role':n[3], 'ip':n[5]})

    return ip