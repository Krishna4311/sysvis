import psutil, socket

addrs = psutil.net_if_addrs()
stats = psutil.net_if_stats()

for name, addr_list in addrs.items():
    ipv4 = ''
    for a in addr_list:
        if a.family == socket.AF_INET:
            ipv4 = a.address
    is_up = stats[name].isup if name in stats else False
    speed = stats[name].speed if name in stats else 0
    print(f'{name:<35} ipv4={ipv4:<16} up={is_up} speed={speed}Mb/s')
