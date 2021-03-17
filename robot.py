from sr.robot import *
import statistics
import math
from collections import defaultdict,deque

R = Robot()

m_left = R.motors[0].m0
m_right = R.motors[0].m1

def set_power(left, right):
    m_left.power = left
    m_right.power = right

def get_heading(n=5):
    heading = 0
    for i in range(0,n):
        heading += R.compass.get_heading()
    return heading/n * (360/math.tau)

def turn(degrees):
    radians = degrees * (math.tau/360)
    if radians != 0:
        per_tenth = 0.43737389828257306 
        sleep_time = math.fabs(radians)/per_tenth/10
        power = 75 
        p = math.copysign(power,radians)
    else:
        p = 0
    print(f"TURN power[{p}] sleep[{sleep_time}]")
    set_power(p,-p)
    R.sleep(sleep_time)

def move(power, distance):
    per_distance = 2
    sleep_time = math.fabs(distance/per_distance)
    p = math.copysign(power,distance)
    print(f"MOVE power[{p}] sleep[{sleep_time}]")
    set_power(p,p)
    R.sleep(sleep_time)

def stop(sleep_time=0.5):
    set_power(0,0)
    R.sleep(sleep_time)

tx_depends = defaultdict(list)
#TODO record the dependecies of the towers

tx_status = defaultdict(dict)
for station_code in StationCode:
    tx_status[station_code]['tx'] = None
    tx_status[station_code]['strength'] = None
    tx_status[station_code]['bearing'] = None
    
def sweep():
    transmitters = R.radio.sweep()
    # Keep the latest sweep code in 'latest'
    tx_status['latest'] = []
    for tx in transmitters:
        station_code = tx.target_info.station_code
        tx_status['latest'].append(station_code)
        # copy the full struct
        tx_status[station_code]['tx'] = tx
        # and the individual values
        tx_status[station_code]['strength'] = tx.signal_strength
        tx_status[station_code]['bearing'] = tx.bearing
        tx_status[station_code]['owner'] = tx.target_info.owned_by
        tx_status[station_code]['locked'] = tx.target_info.locked

def correct_heading(degrees, variance=2):
    heading = get_heading()
    print(f"Current heading: {heading}")
    diff = heading - degrees
    if math.fabs(diff) < variance:
        print("No need to correct")
        return
    print(f"Correcting by {diff} degrees.")
    turn(-diff)
    stop()
    return

# First part by dead-reckoning
print(f"heading = {get_heading(1000)}")
move(75,1.4)
stop()
print(f"heading = {get_heading(1000)}")
turn(-40)
stop()
print(f"heading before correction = {get_heading(1000)}")
correct_heading(116)
print(f"heading = {get_heading(1000)}")
move(75,2.2)
stop(1.0)
correct_heading(116)
R.radio.claim_territory()
print(f"heading = {get_heading(1000)}")
move(100,2.6)
stop(1.5)
correct_heading(116)
R.radio.claim_territory()
print(f"heading = {get_heading(1000)}")
move(100,-5.5)
print(f"heading = {get_heading(1000)}")
stop(1.5)
correct_heading(180)
correct_heading(180)
correct_heading(180)
correct_heading(180)
correct_heading(180)
move(100, 3)