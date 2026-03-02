import json
import os
from datetime import datetime
from enum import verify

from vmanage_api import VmanageRestApi
from dotenv import load_dotenv

def vmanage_login() -> VmanageRestApi:
    load_dotenv()
    username = os.getenv("VMANAGE_USER")
    password = os.getenv("VMANAGE_PASS")
    address = os.getenv("VMANAGE_ADDRESS")
    vmanage = VmanageRestApi(username=username, password=password, vmanage_ip=address)

    return vmanage

def vmanage_logout(vmanage: VmanageRestApi):
    vmanage.logout()

def get_events(vmanage: VmanageRestApi, sys_ip="10.33.205.24", hours=3, last_n=True, start_time=datetime.now(),
               event_name=[], component=[]):

    if last_n:
        entry_time = {
            "value":[str(hours)],
            "field":"entry_time",
            "type":"date",
            "operator":"last_n_hours"
        }
    else:
        timestamp = datetime.fromtimestamp(start_time)
        from_time = (f'{timestamp.year}-{timestamp.month:02}-{timestamp.day:02}T'
                     f'{timestamp.hour:02}:{timestamp.minute:02}:{timestamp.second:02}')
        timestamp = datetime.fromtimestamp(start_time + 3600 * hours)
        to_time = (f'{timestamp.year}-{timestamp.month:02}-{timestamp.day:02}T'
                   f'{timestamp.hour:02}:{timestamp.minute:02}:{timestamp.second:02}')
        entry_time = {
            "field":"entry_time",
            "operator":"between",
            "type":"date",
            "value": [
                from_time,
                to_time
            ]
        }

    payload = {
        "query": {
            "condition":"AND",
            "rules":[
                entry_time,
                {
                   "field":"system_ip",
                   "operator":"in",
                   "type":"string",
                   "value":[sys_ip]
               }
            ]
        }
        ,"size":10000
    }

    if event_name:
        payload["query"]["rules"].append({
            "field": "eventname",
            "operator": "in",
            "type": "string",
            "value": [event_name]
        })

    if component:
        payload["query"]["rules"].append({
            "field": "component",
            "operator": "in",
            "type": "string",
            "value": [component]

        })

    events = vmanage.post_request("/event", payload)
    return events

def get_tunnels(vmanage: VmanageRestApi, site='481157000'):
    tunnels = vmanage.get_request(f'/statistics/tunnelhealth/history?site={site}')
    colors = {}
    for t in tunnels:
        if t['local_color'] not in colors:
            colors[t['local_color']] = {}
        colors[t['local_color']][t['remote_system_ip']] = {}
    return colors

def get_queues(vmanage: VmanageRestApi, sys_ip="10.33.205.24"):
    sla = vmanage.get_request(f'/device/app-route/sla-class?deviceId={sys_ip}')['data']
    queues = []
    for x in sla:
        if x['name'] != '__all_tunnels__':
            queues.append(x['name'])

    return queues


class Events():

    def __init__(self, vmanage, site='481157000'):
        self.site = site
        self.colors = get_tunnels(vmanage=vmanage, site=self.site)
        self.queues = get_queues(vmanage)


if __name__ == '__main__':
    ...
