from sr.robot import *
import statistics
import math
from collections import defaultdict,deque
import numpy
from sklearn.metrics import r2_score
from enum import IntEnum
from pprint import pprint

R = Robot()

zone0 = R.zone == 0
m_left = R.motors[0].m0
m_right = R.motors[0].m1

station_mirror_dict = {
    StationCode.OX: StationCode.BN,
    StationCode.TS: StationCode.SW,
    StationCode.VB: StationCode.SZ,
    StationCode.BG: StationCode.HV,
    StationCode.EY: StationCode.PO,
    StationCode.PN: StationCode.YL,
    StationCode.TH: StationCode.SF,
    StationCode.PL: StationCode.PL,
    StationCode.BE: StationCode.BE,
    StationCode.HA: StationCode.HA,
    StationCode.YT: StationCode.YT,
    StationCode.FL: StationCode.FL,
    StationCode.PO: StationCode.EY,
    StationCode.SZ: StationCode.VB,
    StationCode.SW: StationCode.TS,
    StationCode.YL: StationCode.PN,
    StationCode.HV: StationCode.BG,
    StationCode.SF: StationCode.TH,
    StationCode.BN: StationCode.OX
}

station_score_dict = {
    StationCode.OX: 2,
    StationCode.TS: 2,
    StationCode.VB: 2,
    StationCode.BG: 2,
    StationCode.EY: 2,
    StationCode.PN: 2,
    StationCode.TH: 4,
    StationCode.PL: 2,
    StationCode.BE: 2,
    StationCode.HA: 4,
    StationCode.YT: 8,
    StationCode.FL: 4,
    StationCode.PO: 2,
    StationCode.SZ: 2,
    StationCode.SW: 2,
    StationCode.YL: 2,
    StationCode.HV: 2,
    StationCode.SF: 2,
    StationCode.BN: 2
}

station_pos_dict = {
    StationCode.OX: [-6.6, 3],
    StationCode.TS: [-2.75,2.75],
    StationCode.VB: [-1.95,0.75],
    StationCode.BG: [-4.2, 0],
    StationCode.EY: [-1.95,-0.75],
    StationCode.PN: [-4.2,-1.8],
    StationCode.TH: [-6.6,-3],
    StationCode.PL: [0,3],
    StationCode.BE: [0, 1.5],
    StationCode.HA: [0,0],
    StationCode.YT: [0,-1.5],
    StationCode.FL: [0,-3],
    StationCode.PO: [1.95,-0.75],
    StationCode.SZ: [1.95,0.75],
    StationCode.SW: [2.75,2.75],
    StationCode.YL: [4.2,-1.8],
    StationCode.HV: [4.2,0],
    StationCode.SF: [6.6,-3],
    StationCode.BN: [6.6,3]    
}

def mirror_coords(coord):
    return coord if zone0 else [coord[0],-coord[1]]



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


def get_real_heading():
    x, _, z = R.compass._compass.getValues()
    heading = math.atan2(x, z) % math.tau
    return heading * (360/math.tau)


def turnXX(degrees, power, b, c):
    t = (math.fabs(degrees) - b) / c
    p = math.copysign(power,degrees)
    print(f"TURN power[{p}] sleep[{t}]")
    set_power(p,-p)
    R.sleep(t)    
    return t

def turn25(degrees):
    if math.fabs(degrees) >= 1:
        return turnXX(degrees, 25, -0.5404, 85.86)

def turn50(degrees):
    if math.fabs(degrees) >= 4:
        return turnXX(degrees, 50, -1.597, 174.9)
    else:
        return turn25(degrees)

def turn75(degrees):
    if math.fabs(degrees) >= 15:
        return turnXX(degrees, 75, -9.562, 269.5)
    else:
        return turn50(degrees)

def turn100(degrees):
    if math.fabs(degrees) >= 25:
        return turnXX(degrees, 100, -20.15, 345.2)
    else:
        return turn75(degrees)


def move(power, sleep_time):
    print(f"MOVE power[{power}] sleep[{sleep_time}]")
    set_power(power, power)
    R.sleep(sleep_time)


def stop(sleep_time=0.01):
    set_power(0, 0)
    R.sleep(sleep_time)

tx_depends = defaultdict(list)
#TODO record the dependecies of the towers

tx_status = defaultdict(dict)
for station_code in StationCode:
    tx_status[station_code]['tx'] = None
    tx_status[station_code]['strength'] = None
    tx_status[station_code]['bearing'] = None
    
# set the initial robot pos
last_robot_pos = mirror_coords([0,-7])    

# update the robot pos based on the transmitters
def update_robot_pos():
    ys = []
    xs = []
    weights = []
    heading = get_heading()
    print(f"Robot heading {heading:.0f}")
    for station_code in tx_status['latest']:
        bearing = tx_status[station_code]['bearing']
        distance = tx_status[station_code]['distance']
        angle = (180 + heading + bearing)%360
        print(f"{station_code} Bearing: {bearing:.0f} Distance {distance:.2f}")
        print(f"{station_code} Heading+Bearing: {heading+bearing:.0f} Distance {distance:.2f}")
        print(f"Robot Pos relative to {station_code} is {angle:.0f} degrees {distance:.2f}m")
        x = station_pos_dict[station_code][0] + math.sin(angle/360*math.tau)*distance
        y = station_pos_dict[station_code][1] - math.cos(angle/360*math.tau)*distance
        print(f"Robot at {x:.2f}, {y:.2f}")
        xs.append(x)
        ys.append(y)
        weights.append(1.0/(distance + 0.1))
    if len(xs) < 1:
        return
    x = numpy.average(xs)
    y = numpy.average(ys)
    xw = numpy.average(xs,weights=weights)
    yw = numpy.average(ys,weights=weights)
    print(f"Avg Robot Position {x:.2f},{y:.2f}")
    print(f"Weighted Avg Robot Position {xw:.2f},{yw:.2f}")
    last_robot_pos = [xw,yw]    

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
        tx_status[station_code]['distance'] = signal_strength_to_distance(tx.signal_strength)
        print(f"[{station_code}] - bearing {tx_status[station_code]['bearing']:.2f}  distance - {tx_status[station_code]['distance']:.2f}   strength - {tx_status[station_code]['strength']:.2f}")
    update_robot_pos()

def signal_strength_to_distance(signal_strength):
    x = math.log10(signal_strength)
    distance = -0.1558 * x*x*x + 0.6721 * x*x - 1.238 * x + 1.011
    return distance if distance > 0 else 0


def set_heading(degrees, variance=1,turnfn=turn100):
    heading = get_heading()
    print(f"Current heading: {heading}   Desired heading: {degrees}")
    diff = degrees - heading
    if math.fabs(diff) < variance:
        print("No need to correct")
        return 0
    print(f"Correcting by {diff} degrees.")    
    return turnfn(diff)

def mirror(degrees):
    return degrees if zone0 else 360 - degrees


set_power(5,100)
R.sleep(0.45)
move(100,2)
stop()
sweep()
# stop(1.9)

R.radio.begin_territory_claim()
turn_time = set_heading(265,turnfn=turn25)
turn_time += set_heading(265,turnfn=turn25)
turn_time += set_heading(265,turnfn=turn25)
print(f"Saved {turn_time} seconds")
stop(2 - turn_time)
R.radio.complete_territory_claim()

sweep()
move(100,2.95)
stop(0.1)
R.radio.begin_territory_claim()
stop(1)
sweep()
stop(1)
R.radio.complete_territory_claim()


