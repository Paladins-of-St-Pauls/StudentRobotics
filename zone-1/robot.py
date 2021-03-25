from sr.robot import *
import statistics
import math
from collections import defaultdict, deque
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
    for i in range(0, n):
        heading += R.compass.get_heading()
    return heading/n * (360/math.tau)


def get_real_heading():
    x, _, z = R.compass._compass.getValues()
    heading = math.atan2(x, z) % math.tau
    return heading * (360/math.tau)


def turnXX(degrees, power, b, c):
    t = (math.fabs(degrees) - b) / c
    p = math.copysign(power, degrees)
    print(f"TURN power[{p}] sleep[{t}]")
    set_power(p, -p)
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


def move(power, sleep_time):
    print(f"MOVE power[{power}] sleep[{sleep_time}]")
    set_power(power, power)
    R.sleep(sleep_time)


def stop(sleep_time=0.01):
    set_power(0, 0)
    R.sleep(sleep_time)


tx_depends = defaultdict(list)
# TODO record the dependecies of the towers

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
        tx_status[station_code]['distance'] = signal_strength_to_distance(tx.signal_strength)
        # print(
        #     f"[{station_code}] - bearing {tx_status[station_code]['bearing']}  distance - {distance}")


def signal_strength_to_distance(signal_strength):
    x = math.log10(signal_strength)
    distance = -0.1558 * x*x*x + 0.6721 * x*x - 1.238 * x + 1.011
    return distance if distance > 0 else 0


def set_heading(degrees, variance=1):
    heading = get_heading()
    # print(f"Current heading: {heading}   Desired heading: {degrees}")
    diff = degrees - heading
    if math.fabs(diff) < variance:
        # print("No need to correct")
        return
    # print(f"Correcting by {diff} degrees.")
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


# sweep()
# move(25,3.1)
# stop()
# set_heading(mirror(180))
strengths = []


print(f"Real Heading - {get_real_heading()}")

for i in range(0, 100):
    set_heading(mirror(180))
    move(20, 0.3)
    stop(0.001)

    sum_strength = 0.0
    for j in range(0, 5):
        sweep()
        if StationCode.BN in tx_status['latest']:
            strength = (tx_status[tx_status['latest'][0]]['strength'])
        else:
            strength = 0
        # print(j, strength)
        sum_strength += strength
    avg_strength = sum_strength/50.0

    strengths.append(avg_strength)

    # if StationCode.BN in tx_status['latest']:
    #     strengths.append(tx_status[tx_status['latest'][0]]['strength'])
    # else:
    #     strengths.append(0.0)

    if front_bumper():
        break

l = len(strengths)

distances = [3.0 - i/float(l)*3.0 for i in range(0, l)]

first_non_zero_index = 0
for i in range(0, l):
    if strengths[i] > 0.00001:
        first_non_zero_index = i
        break

strengths = strengths[first_non_zero_index+1:-1]
distances = distances[first_non_zero_index+1:-1]

strengths.reverse()
distances.reverse()

print(strengths)
print(distances)


# m1 = numpy.poly1d(numpy.polyfit(distances,strengths,1))
# r1 = r2_score(strengths, m1(distances))
# print(f"Poly 1 - \n{m1}  - R2 {r1}")
# m2 = numpy.poly1d(numpy.polyfit(distances,strengths,2))
# r2 = r2_score(strengths, m2(distances))
# print(f"Poly 2 - \n{m2}  - R2 {r2}")
# m3 = numpy.poly1d(numpy.polyfit(distances,strengths,3))
# r3 = r2_score(strengths, m3(distances))
# print(f"Poly 3 - \n{m3}  - R2 {r3}")

# print("LOG1")

# m1 = numpy.poly1d(numpy.polyfit(numpy.log(distances),strengths,1))
# r1 = r2_score(strengths, m1(numpy.log(distances)))
# print(f"Poly 1 LOG1 - \n{m1}  - R2 {r1}")
# m2 = numpy.poly1d(numpy.polyfit(numpy.log(distances),strengths,2))
# r2 = r2_score(strengths, m2(numpy.log(distances)))
# print(f"Poly 2 LOG1 - \n{m2}  - R2 {r2}")
# m3 = numpy.poly1d(numpy.polyfit(numpy.log(distances),strengths,3))
# r3 = r2_score(strengths, m3(numpy.log(distances)))
# print(f"Poly 3 LOG1 - \n{m3}  - R2 {r3}")

# m1 = numpy.poly1d(numpy.polyfit((distances),numpy.log(strengths),1))
# r1 = r2_score(numpy.log(strengths), m1((distances)))
# print(f"Poly 1 LOGn - \n{m1}  - R2 {r1}")
# m2 = numpy.poly1d(numpy.polyfit((distances),numpy.log(strengths),2))
# r2 = r2_score(numpy.log(strengths), m2((distances)))
# print(f"Poly 2 LOGn - \n{m2}  - R2 {r2}")
# m3 = numpy.poly1d(numpy.polyfit((distances),numpy.log(strengths),3))
# r3 = r2_score(numpy.log(strengths), m3((distances)))
# print(f"Poly 3 LOGn - \n{m3}  - R2 {r3}")


# m1 = numpy.poly1d(numpy.polyfit((distances),numpy.log2(strengths),1))
# r1 = r2_score(numpy.log2(strengths), m1((distances)))
# print(f"Poly 1 LOG2 - \n{m1}  - R2 {r1}")


# m1 = numpy.poly1d(numpy.polyfit((distances),numpy.log1p(strengths),1))
# r1 = r2_score(numpy.log1p(strengths), m1((distances)))
# print(f"Poly 1 log1p - \n{m1}  - R2 {r1}")

# m1 = numpy.poly1d(numpy.polyfit((distances),numpy.log10(strengths),1))
# r1 = r2_score(numpy.log10(strengths), m1((distances)))
# print(f"Poly 1 LOG10 - \n{m1}  - R2 {r1}")
# m2 = numpy.poly1d(numpy.polyfit((distances),numpy.log10(strengths),2))
# r2 = r2_score(numpy.log10(strengths), m2((distances)))
# print(f"Poly 2 LOG10 - \n{m2}  - R2 {r2}")
# m3 = numpy.poly1d(numpy.polyfit((distances),numpy.log10(strengths),3))
# r3 = r2_score(numpy.log10(strengths), m3((distances)))
# print(f"Poly 3 LOG10 - \n{m3}  - R2 {r3}")

m1 = numpy.poly1d(numpy.polyfit(numpy.log10(strengths), (distances), 1))
r1 = r2_score(distances, m1((numpy.log10(strengths))))
print(f"Poly 3 LOG10r - \n{m1}  - R2 {r1}")

m2 = numpy.poly1d(numpy.polyfit(numpy.log10(strengths), (distances), 2))
r2 = r2_score(distances, m2((numpy.log10(strengths))))
print(f"Poly 3 LOG10r - \n{m2}  - R2 {r2}")

m3 = numpy.poly1d(numpy.polyfit(numpy.log10(strengths), (distances), 3))
r3 = r2_score(distances, m3((numpy.log10(strengths))))
print(f"Poly 3 LOG10r - \n{m3}  - R2 {r3}")
# print(dist_fl)
# print(dist_fr)
# print(dist_l)
