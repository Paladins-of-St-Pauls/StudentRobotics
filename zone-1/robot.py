from sr.robot import *
import statistics
import math
from collections import defaultdict,deque
import numpy
from sklearn.metrics import r2_score
from enum import IntEnum

R = Robot()

zone0 = R.zone == 0
m_left = R.motors[0].m0
m_right = R.motors[0].m1



def front_bumper():
    return R.ruggeduinos[0].digital_read(2)

def back_bumper():
    return R.ruggeduinos[0].digital_read(3)

class LED(IntEnum):
    RIGHT_RED = 4
    RIGHT_GREEN = 5
    RIGHT_BLUE = 6
    LEFT_BLUE = 7
    LEFT_GREEN = 8
    LEFT_RED = 9

def led(led_enum, state):
    R.ruggeduinos[0].digital_write(led_enum, state)

class SENSOR(IntEnum):
    FRONT_LEFT = 0
    FRONT_RIGHT = 1
    LEFT = 2
    RIGHT = 3
    BACK_LEFT = 4
    BACK_RIGHT = 5    

def distance(sensor_enum):
    return R.ruggeduinos[0].analogue_read(sensor_enum)

def set_power(left, right):
    m_left.power = left
    m_right.power = right

def get_heading(n=5):
    heading = 0
    for i in range(0,n):
        heading += R.compass.get_heading()
    return heading/n * (360/math.tau)


def turnXX(degrees, power, b, c):
    t = (math.fabs(degrees) - b) / c
    p = math.copysign(power,degrees)
    print(f"TURN power[{p}] sleep[{t}]")
    set_power(p,-p)
    R.sleep(t)    

def turn25(degrees):
    if math.fabs(degrees) >= 1:
        turnXX(degrees, 25, -0.5404, 85.86)

def turn50(degrees):
    if math.fabs(degrees) >= 4:
        turnXX(degrees, 50, -1.597, 174.9)
    else:
        turn25(degrees)

def turn75(degrees):
    if math.fabs(degrees) >= 15:
        turnXX(degrees, 75, -9.562, 269.5)
    else:
        turn50(degrees)

def turn100(degrees):
    if math.fabs(degrees) >= 25:
        turnXX(degrees, 100, -20.15, 345.2)
    else:
        turn75(degrees)

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
        tx_status[station_code]['bearing'] = tx.bearing * 360 / math.tau
        tx_status[station_code]['owner'] = tx.target_info.owned_by
        print(f"[{station_code}] - bearing {tx_status[station_code]['bearing']}  strength - {tx.signal_strength}")

def set_heading(degrees, variance=2):
    heading = get_heading()
    print(f"Current heading: {heading}   Desired heading: {degrees}")
    diff = degrees - heading
    if math.fabs(diff) < variance:
        print("No need to correct")
        return
    print(f"Correcting by {diff} degrees.")
    turn50(diff)
    stop()
    return

def mirror(degrees):
    return degrees if zone0 else 360 - degrees


# First part by dead-reckoning
# set_heading(mirror(143))
# print(f"heading = {get_heading(1000)}")
# move(75,0.5)
# stop()
# print(f"heading = {get_heading(1000)}")

# print(f"heading before correction = {get_heading(1000)}")
# set_heading(mirror(116))
# print(f"heading = {get_heading(1000)}")
# move(75,3.2)
# stop(1.0)
# set_heading(mirror(116))
# R.radio.claim_territory()
# print(f"heading = {get_heading(1000)}")
# move(100,2.6)
# stop(1.5)
# set_heading(mirror(116))
# R.radio.claim_territory()
# print(f"heading = {get_heading(1000)}")
# move(100,-5.5)
# print(f"heading = {get_heading(1000)}")
# stop(1.5)
# set_heading(180)
# move(50, 0.1)
# set_heading(180)
# move(100, 1.5)

sweep()
move(25,3.1)
stop()
set_heading(mirror(180))
strengths=[]
for i in range(0,50):
    set_heading(mirror(180))
    move(25,0.4)
    stop()
    sweep()

    print(f"Distance[L,R] = {distance(SENSOR.FRONT_LEFT)}, {distance(SENSOR.FRONT_RIGHT)}")

    if front_bumper():
        break

    if StationCode.BN in tx_status['latest']:
        led(LED.LEFT_BLUE,True)
        print(tx_status['latest'])
        strengths.append(tx_status[tx_status['latest'][0]]['strength'])
    else:
        led(LED.LEFT_BLUE,False)
        strengths.append(0.0)

print(strengths)

