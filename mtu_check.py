
# Does a Tunnel MTU check for reduced tunnels
# Lists out headends by looking for model specified below as 'headend_model'
# Once a user selects a headend, it lists all tunnels less than 'expected_mtu'
# along with the corresponding MTU from the branch side.

import vmanage_events as v

headend_model = 'vedge-C8500-12X4QC'
expected_mtu = 1438

vm = v.vmanage_login()

# Get a list of all edges and headends
devices = vm.get_request('/device')['data']
edges = {}
headends = []
for device in devices:
    edges[device['deviceId']] = device['host-name']
    if device['device-model'] == headend_model:
        headends.append({'system-ip': device['deviceId'], 'host-name': device['host-name']})
for num, headend in enumerate(headends):
    print(f"{num}: {headend['host-name']}")
headend_choice = int(input('Choose a headend: '))
device_id = headends[headend_choice]['system-ip']

# Pull BFD list for the selected Headend and compile a list of 'tunnels' with less than expected MTU
bfds = vm.get_request(f'/device/tunnel/statistics?deviceId={device_id}')['data']
tunnels = []
for headend_bfd in bfds:
    if headend_bfd['tunnel-mtu'] < expected_mtu:
        tunnel_stats = {}
        for stat in ['vdevice-name', 'system-ip', 'local-color', 'remote-color', 'tunnel-mtu']:
            tunnel_stats[stat] = headend_bfd[stat]
        tunnels.append(tunnel_stats)
print(f"Found {len(tunnels)} tunnels")
tunnels = sorted(tunnels, key=lambda tunnel: tunnel['system-ip'])

# Print a list of the found tunnels and query branch for branch side MTU
for headend_bfd in tunnels:
    bfds = vm.get_request(f"/device/tunnel/statistics?deviceId={headend_bfd['system-ip']}")['data']
    for branch_bfd in bfds:
        if branch_bfd['local-color'] == headend_bfd['remote-color'] and \
            branch_bfd['system-ip'] == headend_bfd['vdevice-name']:
            print(f"{edges[branch_bfd['vdevice-name']]:}:{branch_bfd['local-color']:16} "
                  f"Headend MTU:{headend_bfd['tunnel-mtu']:>4}  Branch MTU:{branch_bfd['tunnel-mtu']:>4}")
            headend_bfd['reverse-mtu'] = branch_bfd['tunnel-mtu']



