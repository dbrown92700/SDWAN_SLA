# SLA Reporting Tool

## Overview
The goal of this tool is to view historical information around SDWAN Tunnel SLA and what traffic
classes are out of SLA over time.

The report works by pulling SLA Events from the event log from the selected edge for the selected
time period.  For multi-BFD tunnels the report displays the percentage of time that an SLA class
is removed from a tunnel for each time period.

![img.png](img.png)

## Installation
>git clone 