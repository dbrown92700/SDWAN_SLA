from urllib3.util.wait import poll_wait_for_socket

import vmanage_events as v
from datetime import datetime
import csv
import time
import json

vmanage = v.vmanage_login()
devices = vmanage.get_request('/device')
edges = []
for d in devices['data']:
    if d['device-type'] == 'vedge':
        edges.append({'sys-ip': d['system-ip'], 'hostname': d['host-name']})
date = datetime.now()
end_time = f'0:00 {date.month}/{date.day}/{date.year}'
start_time = int(datetime.timestamp(datetime.strptime(end_time, '%H:%M %m/%d/%Y')) - 7*24*3600)
for num, e in enumerate(edges):
    total_events = 0
    for days in range(0, 7):
        poll_time = start_time + days * 24 * 3600
        success = False
        while not success:
            try:
                events = len(v.get_events(vmanage, sys_ip=e['sys-ip'], last_n=False, hours=24, start_time=poll_time, event_name='sla-change')['data'])
                success = True
            except json.decoder.JSONDecodeError:
                v.vmanage_logout(vmanage)
                print(f'API Error on {e["sys-ip"]}. 5 second pause.')
                time.sleep(5)
                vmanage = v.vmanage_login()
        poll_time = datetime.fromtimestamp(poll_time)
        e[f'{poll_time.month}/{poll_time.day}'] = events
        total_events += events
    e['total_events'] = total_events
    print(num, len(edges), e)
sorted_edges = sorted(edges, key=lambda e: e['total_events'], reverse=True)
for e in range(-1, -11, -1):
    print(f'{sorted_edges[e]["hostname"]} {sorted_edges[e]["total_events"]}')
    print(sorted_edges[e])
t = datetime.now()
with open(f'SLA_Totals-{t.year}{t.month}{t.day}.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=list(sorted_edges[0].keys()))
    writer.writeheader()
    writer.writerows(sorted_edges)
