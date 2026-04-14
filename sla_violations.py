import vmanage_events as v
import json
from datetime import datetime

gmt_adjust = 5 * 3600
last_n = True
time_range = 24
last_N = 'y'
now = datetime.now()
entered_time = f'0:00 {now.month}/{now.day}/{now.year}'
sys_ip = '10.1.1.1'

sys_ip = input(f'\n\nEnter system ip {sys_ip}: ') or sys_ip
time_range = int(input(f'Enter number of hours to query [{time_range}]: ') or time_range)
last_N = input(f'Show "last N" hours? Enter "n" to enter a start time [{last_N}]: ') or last_N
if last_N == 'y':
    last_n = True
if last_N == 'n':
    last_n = False
    entered_time = (input(f'Enter start time and date using 24-hour time in the format [{entered_time}]: ') or
                    entered_time)
start_time = datetime.timestamp(datetime.strptime(entered_time, '%H:%M %m/%d/%Y'))
if (last_n):
    tm = datetime.fromtimestamp(datetime.now().timestamp() - time_range * 3600)
else:
    tm = datetime.strptime(entered_time, '%H:%M %m/%d/%Y')
file_time = f'{tm.year}{tm.month:02}{tm.day:02}{tm.hour:02}{tm.minute:02}'

vmanage = v.vmanage_login()
events = v.get_events(vmanage, hours=time_range, last_n=last_n, start_time=start_time + gmt_adjust, sys_ip=sys_ip,
                      event_name='sla-violation')['data']
print(f'Number of Events: {len(events)}')
t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
with open(f'sla_violations_{sys_ip}_{datetime.now().strftime('%Y%m%d%H%M')}.csv', 'w') as outfile:
    outfile.write('Time,VPN,Class,Application\n')
    for e in events:
        time = datetime.fromtimestamp(e['entry_time']/1000).strftime('%Y/%m/%d %H:%M:%S')
        ev = json.loads(e['event'])['sla-violation']
        try:
            outfile.write(f"{time},{ev['vpn-id']},{ev['sla-information'].split(',')[0].removeprefix('Class: ')},"
                          f"{ev['application']}\n")
        except KeyError:
            print(ev)
vmanage.logout()