import vmanage_events as v
import json
from datetime import datetime

# 10.33.205.24

time_range = 3
last_n = True
period = 900
entered_time = '9:00 2/25/2026'
start_time = datetime.strptime(entered_time, '%H:%M %m/%d/%Y')


def print_queues(tunnels):
    times = ''
    for t in range(int(time_range * 3600 / period)):
        time = datetime.fromtimestamp(start_time + period * t)
        times += f'{time.hour:02}:{time.minute:02} '
    for c in tunnels:
        print(f'{"Color":16}{"Remote sys-ip":16}{"Queue":7} {times}')
        for t in tunnels[c]:
            for q in queues:
                stats = ''
                for h in tunnels[c][t][1][q]:
                    if h == period:
                        stats += '    - '
                    else:
                        stats += f'{100 - int(h * 100 / period):5} '
                print(f'{c:16}{t:16}{q:7} {stats}')

def print_tunnel_events(color, rip):
    for x in sla_events:
        if x['event']['local-color'] == color and x['event']['remote-system-ip'] == rip:
            print(datetime.fromtimestamp(int(x['statcycletime'] / 1000)))
            print(x['event'])

if __name__ == '__main__':

    last_n = True
    time_range = 3
    last_N = 'y'
    now = datetime.now()
    entered_time = f'0:00 {now.month}/{now.day}/{now.year}'
    period_choice = '1'
    sys_ip = '10.1.1.1'

    vmanage = v.vmanage_login()

    while True:
        sys_ip = input(f'\n\nEnter system ip {sys_ip} (or q to quit): ') or sys_ip
        if sys_ip == 'q':
            vmanage.logout()
            exit(0)
        time_range = int(input(f'Enter number of hours to display [{time_range}]: ') or 3)
        last_N = input(f'Show "last N" hours? Enter "n" to enter a start time [{last_N}]: ') or last_N
        if last_N == 'n':
            last_n = False
            entered_time = input(f'Enter start time and date using 24-hour time in the format [{entered_time}]: ') or entered_time
            start_time = datetime.timestamp(datetime.strptime(entered_time, '%H:%M %m/%d/%Y'))
        period_choice = input(f'Enter period choice\n1: Hour\n2: 30 minutes\n3: 15 minutes\n[{period_choice}]? ') or period_choice
        period = {'1': 3600, '2': 1800, '3': 900}[period_choice]

        device = vmanage.get_request(f'/device?deviceId={sys_ip}')
        site_id = device['data'][0]['site-id']

        # Get Events
        sla_events = v.get_events(vmanage, last_n=last_n, hours=time_range, start_time=start_time, event_name='sla-change')
        if last_n:
            start_time = int(sla_events['header']['generatedOn']/1000) - time_range * 3600
        sla_events = sla_events['data']
        sla_events.reverse()
        for x in sla_events:
            x['event'] = json.loads(x['event'])[x['eventname']]

        print(f'\nSLA Report\nSystemIP: {sys_ip}   SiteID {site_id}    SLA Events: {len(sla_events)}\n')

        # initialize data structure
        tunnels = v.get_tunnels(vmanage, site=site_id)
        queues = v.get_queues(vmanage, sys_ip=sys_ip)

        for color in tunnels:
            for rip in tunnels[color]:
                q = [0, {q: [0 for x in range(int(time_range*3600/period))] for q in queues}]
                tunnels[color][rip] = q

        # parse events
        for event in sla_events:

            e = event['event']

            old_q = e['old-sla-classes'].split(', ')
            new_q = e['sla-classes'].split(', ')

            event_tunnel = tunnels[e['local-color']][e['remote-system-ip']]

            event_time = int(event['entry_time'] / 1000) - start_time
            if event_time == time_range * 3600:
                event_time -= 1
            event_hour = int(event_time / period)
            event_seconds = event_time % period
            tunnel_last_event_time = event_tunnel[0]
            tunnel_last_event_hour = int(tunnel_last_event_time / period)
            event_tunnel[0] = event_time

            if tunnel_last_event_time == 0:
                # first event on this tunnel
                if old_q != ['None']:
                    for queue in old_q:
                        # for queues that were in SLA
                        time_list = event_tunnel[1][queue]
                        for t in range(event_hour):
                            # fill in all fully elapsed hours
                            time_list[t] = period
                        # put remaining time in next hour
                        time_list[event_hour] = event_seconds
                event_tunnel.append(new_q)
            else:
                # later event on this tunnel
                if old_q != ['None']:
                    for queue in old_q:
                        # if queue was in SLA, credit it for elapsed time
                        time_list = event_tunnel[1][queue]
                        if tunnel_last_event_hour == event_hour:
                            time_list[event_hour] += event_time - tunnel_last_event_time
                        else:
                            time_list[tunnel_last_event_hour] += (tunnel_last_event_hour + 1) * period - tunnel_last_event_time
                            for t in range(tunnel_last_event_hour + 1, event_hour):
                                # fill in all fully elapsed hours
                                time_list[t] = period
                        # put remaining time in next hour
                        time_list[event_hour] = event_seconds
                event_tunnel[2] = new_q

        # Fill in remaining time for Queues in SLA on last event
        for c in tunnels:
            for t in tunnels[c]:
                last_event_time = tunnels[c][t][0]
                last_event_hour = int(last_event_time / period)
                # Calculate remainder seconds.  If event happened on an hour boundry seconds should be 3600.
                last_event_seconds = (time_range * 3600 - last_event_time) % period or period
                try:
                    # Get queues in SLA on last time period
                    new_q = tunnels[c][t][2]
                except IndexError:
                    # If there's no entry, there were no events. Assume all queues were in SLA
                    new_q = queues
                if new_q != ['None']:
                    for q in new_q:
                        time_list = tunnels[c][t][1][q]
                        time_list[last_event_hour] += last_event_seconds
                        for time in range(last_event_hour + 1, int(time_range*3600/period)):
                            time_list[time] = period

        print_queues(tunnels)

        # print_tunnel_events(color = 'public-internet', rip = '10.46.16.55')

