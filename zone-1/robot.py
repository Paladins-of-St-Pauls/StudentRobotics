from sr.robot import *
import statistics
import math
from collections import defaultdict, deque
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
    StationCode.TS: [-2.75, 2.75],
    StationCode.VB: [-1.95, 0.75],
    StationCode.BG: [-4.2, 0],
    StationCode.EY: [-1.95, -0.75],
    StationCode.PN: [-4.2, -1.8],
    StationCode.TH: [-6.6, -3],
    StationCode.PL: [0, 3],
    StationCode.BE: [0, 1.5],
    StationCode.HA: [0, 0],
    StationCode.YT: [0, -1.5],
    StationCode.FL: [0, -3],
    StationCode.PO: [1.95, -0.75],
    StationCode.SZ: [1.95, 0.75],
    StationCode.SW: [2.75, 2.75],
    StationCode.YL: [4.2, -1.8],
    StationCode.HV: [4.2, 0],
    StationCode.SF: [6.6, -3],
    StationCode.BN: [6.6, 3]
}


def mirror_station(station_code):
    return station_code if zone0 else station_mirror_dict[station_code]


def mirror_coords(coord):
    return coord if zone0 else [-coord[0], coord[1]]


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
# TODO record the dependecies of the towers

tx_status = defaultdict(dict)
for station_code in StationCode:
    tx_status[station_code]['tx'] = None
    tx_status[station_code]['strength'] = None
    tx_status[station_code]['bearing'] = None

# set the initial robot pos
last_robot_pos = mirror_coords([-7, 0])
last_robot_pos_list = deque(maxlen=3)
last_robot_pos_list.append(0.0)

# update the robot pos based on the transmitters


def update_robot_pos():
    global last_robot_pos
    ys = []
    xs = []
    weights = []
    heading = get_heading()
    # print(f"Robot heading {heading:.0f}")
    for station_code in tx_status['latest']:
        bearing = tx_status[station_code]['bearing']
        distance = tx_status[station_code]['distance']
        angle = (180 + heading + bearing) % 360
        # print(f"{station_code} Bearing: {bearing:.0f} Distance {distance:.2f}")
        # print(f"{station_code} Heading+Bearing: {heading+bearing:.0f} Distance {distance:.2f}")
        # print(f"Robot Pos relative to {station_code} is {angle:.0f} degrees {distance:.2f}m")
        x = station_pos_dict[station_code][0] + \
            math.sin(angle/360*math.tau)*distance
        y = station_pos_dict[station_code][1] - \
            math.cos(angle/360*math.tau)*distance
        # print(f"Robot at {x:.2f}, {y:.2f}")
        xs.append(x)
        ys.append(y)
        weights.append(1.0/(distance + 0.1))
    if len(xs) < 1:
        return
    x = numpy.average(xs)
    y = numpy.average(ys)
    xw = numpy.average(xs, weights=weights)
    yw = numpy.average(ys, weights=weights)
    # print(f"Avg Robot Position {x:.2f},{y:.2f}")
    print(f"Weighted Avg Robot Position {xw:.2f},{yw:.2f}")
    distance_moved_since_last_update = get_distance(last_robot_pos, [xw, yw])
    last_robot_pos = [xw, yw]
    last_robot_pos_list.append(distance_moved_since_last_update)
    print(f"Distance robot moved = {last_robot_pos_list}")


def not_moving():
    avg_distance = sum(last_robot_pos_list)/len(last_robot_pos_list)
    return avg_distance < 0.05


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
        tx_status[station_code]['distance'] = signal_strength_to_distance(
            tx.signal_strength)
        print(f"[{station_code}] - bearing {tx_status[station_code]['bearing']:.2f}  distance - {tx_status[station_code]['distance']:.2f}   strength - {tx_status[station_code]['strength']:.2f}")
    update_robot_pos()


def signal_strength_to_distance(signal_strength):
    if signal_strength > 0:
        x = 1.0 / math.sqrt(signal_strength)
        distance = 0.9795 * x - 0.0142
        return distance if distance > 0.0 else 0.0
    # A big number for errors but not too big
    return 100.0


def set_heading(degrees, variance=1, turnfn=turn100, max_diff=None):
    heading = get_heading()
    print(f"Current heading: {heading}   Desired heading: {degrees}")
    diff = (180 + degrees - heading) % 360 - 180
    if math.fabs(diff) < variance:
        print("No need to correct")
        return 0
    if max_diff is not None and math.fabs(diff) > max_diff:
        print(f"Turn ({diff}) greater than {max_diff}, limiting to {max_diff}")
        diff = max_diff if diff > 0 else -max_diff

    print(f"Correcting by {diff} degrees.")
    return turnfn(diff)


def move_to_bearing(power, sleep_time, bearing):
    print(
        f"move_to_bearing: power:{power:.0f} time:{sleep_time:0.2f} bearing:{bearing:.1f}")
    scale = 1.0 - math.fabs(bearing)/90
    if bearing > 0:
        set_power(power, scale*power)
    else:
        set_power(scale*power, power)
    R.sleep(sleep_time)


def mirror(degrees):
    return degrees if zone0 else (360 - degrees) % 360


def get_distance(p1, p2):
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    return math.sqrt(dx*dx + dy*dy)


def get_absolute_bearing(p1, p2):
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    # print(f"p1:{p1}  p2:{p2}  dx:{dx} dy:{dy} (math.atan2(dx, -dy) % math.tau) * (360/math.tau):{(math.atan2(dx, -dy) % math.tau) * (360/math.tau)}")
    return (math.atan2(dx, -dy) % math.tau) * (360/math.tau)


def get_bearing(p1, p2):
    heading = get_heading()
    absolute_bearing = get_absolute_bearing(p1, p2)
    relative_bearing = (180 + absolute_bearing - heading) % 360 - 180
    # print(f" heading:{heading} abs_bearing:{absolute_bearing} rel_bearing:{relative_bearing}")
    return relative_bearing


def get_bearing_distance_strength(station_code):
    if not station_code in tx_status['latest']:
        print(
            f"Can't see {station_code} using last known robot pos {last_robot_pos} and location of station {station_code} {station_pos_dict[station_code]}")
        # We can't see the station but we can estimate the direction to go based
        # on our last known position and the location of the tower
        bearing = get_bearing(last_robot_pos, station_pos_dict[station_code])
        distance = get_distance(last_robot_pos, station_pos_dict[station_code])
        strength = 0
    else:
        bearing = tx_status[station_code]['bearing']
        strength = tx_status[station_code]['strength']
        distance = tx_status[station_code]['distance']
    return bearing, distance, strength

def go_to_station_exceptions(station_code, prev_station_code):
    if prev_station_code == mirror_station(StationCode.BG) and station_code ==  mirror_station(StationCode.PL):
        print(f"###########{prev_station_code}------>{station_code}##############################")
        # extra careful to avoid the obstacle
        stop()
        rotate_to_target_bearing(mirror(134))
        move(100,0.1)

    if prev_station_code == mirror_station(StationCode.SW) and station_code ==  mirror_station(StationCode.HV):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_station_code}------>{station_code}##############################")
            rotate_to_target_bearing(mirror(0))
            stop()
            move(100,1.2)

    if prev_station_code == mirror_station(StationCode.HV) and station_code ==  mirror_station(StationCode.PO):
        # Here we need to be careful of the centre wall         
        print(f"###########{prev_station_code}------>{station_code}##############################")
        stop()
        rotate_to_target_bearing(mirror(270))
        stop()
        move(100,0.1)
        stop()
        rotate_to_target_bearing(mirror(0))
        stop()
        move(100,0.5)
        stop()

    if prev_station_code == mirror_station(StationCode.BG) and station_code ==  mirror_station(StationCode.VB):
        # Here we need to be careful of the centre wall         
        print(f"###########{prev_station_code}------>{station_code}##############################")
        stop()
        rotate_to_target_bearing(mirror(180))
        stop()
        move(100,0.5)
        stop()

def rotate_to_target_bearing(target_heading, close_enough_angle=4, start_claim_time=None):
    current_heading = get_heading()
    diff_heading = diff_bearing(target_heading, current_heading)
    print(f"Rotating to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
    max_iterations = 15
    iterations = 0
    while math.fabs(diff_heading) > close_enough_angle:
        power = min(100,diff_heading * 180 / 180 + math.copysign(10,diff_heading))
        print(f"Rotating with power {power:.0f} to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
        set_power(power,-power)
        R.sleep(0.04)    
        current_heading = get_heading()
        diff_heading = diff_bearing(target_heading, current_heading)
        # If the claim time has elapsed break the while loop
        if start_claim_time and R.time() - start_claim_time > 1.95:
            print("Exiting turn early, claim time expiring")
            break
        # If we have done too many iterations(possibly stuck while turning) break the while loop
        iterations += 1
        if iterations > max_iterations:
            print("Exiting turn early, we are probably stuck")
            break


def go_to_station(station_code, prev_station_code):
    go_to_station_exceptions(station_code, prev_station_code)
    sweep()
    bearing, distance, strength = get_bearing_distance_strength(station_code)
    print(f"Go to {station_code} - bearing {bearing:.2f}  distance - {distance:.2f}   strength - {strength:.2f}")
    while strength < 4.2:
        move_to_bearing(100, 0.1, bearing)
        # move(100, 0.2 if strength < 1.5 else 0.1)
        sweep()
        bearing, distance, strength = get_bearing_distance_strength(
            station_code)
        print(
            f"Go to {station_code} - bearing {bearing:.2f}  distance - {distance:.2f}   strength - {strength:.2f}")
        if front_bumper() or not_moving():
            if front_bumper():
                print("stuck - front bumper pressed")
            else:
                print("stuck - not moving")
            move(-100, 0.35)
            stop()
            sweep()
            bearing, distance, strength = get_bearing_distance_strength(
                station_code)
            heading = get_heading()
            set_heading(heading + bearing)

    print(f"Arrived at {station_code}")
    return True


def ismine(station_code):
    mine = Claimant.ZONE_0 if zone0 else Claimant.ZONE_1
    if station_code in tx_status and 'owner' in tx_status[station_code]:
        return tx_status[station_code]['owner'] == mine
    return False


def istheirs(station_code):
    theirs = Claimant.ZONE_1 if zone0 else Claimant.ZONE_0
    if station_code in tx_status and 'owner' in tx_status[station_code]:
        return tx_status[station_code]['owner'] == theirs
    return False


def isunclaimed(station_code):
    if station_code in tx_status and 'owner' in tx_status[station_code]:
        return tx_status[station_code] is None
    return False

def diff_bearing(a, b):
    return (180 + a - b) % 360 - 180

def claim_station(station_code, next_station_code):
    # It looks like you cannot take more than 2.x seconds claiming
    start_claim_time = R.time()
    if not ismine(station_code):
        print(
            f"Starting claim of {station_code}, next_station_code={next_station_code} at time {start_claim_time}")
        R.radio.begin_territory_claim()

    # Stop and sweep - allow the stop to stabilise our position before we sweep
    stop(0.2)
    sweep()

    # Make sure we back up a bit so that we can turn around the station without colliding with it.
    bearing, distance, strength = get_bearing_distance_strength(station_code)
    target_distance = 0.22
    while distance < target_distance:
        target_diff =  target_distance - distance
        print(f'Moving Back to {target_distance}, {target_diff:.2f} to go - wait time {R.time()-start_claim_time}')
        move(-10-(target_diff*70), 0.1)
        sweep()
        bearing, distance, strength = get_bearing_distance_strength(station_code)
        if R.time() - start_claim_time > 1.95:
            break        
    stop()

    # Start to turn towards the next station, also check where the current station is.
    # If the current and the next are in the same general direction, then turn a bit more 
    # so that we can get around the current station
    next_station_bearing = get_absolute_bearing(
        last_robot_pos, station_pos_dict[next_station_code])
    target_heading = next_station_bearing

    current_station_bearing = get_absolute_bearing(
        last_robot_pos, station_pos_dict[station_code])

    diff_danger_angle = 45
    diff_station_bearing = diff_bearing(next_station_bearing, current_station_bearing)
    if math.fabs(diff_station_bearing) < diff_danger_angle:
        print(f"Difference in bearing between {station_code}({current_station_bearing:.0f}) and {next_station_code}({next_station_bearing:.0f})")
        target_heading += math.copysign(diff_danger_angle,diff_station_bearing)

    close_enough_angle = 4
    current_heading = get_heading()
    diff_heading = diff_bearing(target_heading, current_heading)
    print(f"Rotating to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
    while math.fabs(diff_heading) > close_enough_angle:
        power = min(100,diff_heading * 180 / 180 + math.copysign(10,diff_heading))
        print(f"Rotating with power {power:.0f} to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
        set_power(power,-power)
        R.sleep(0.05)    
        current_heading = get_heading()
        diff_heading = diff_bearing(target_heading, current_heading)
        if R.time() - start_claim_time > 1.95:
            break
    stop()
    print(f"Current Heading {get_heading():.0f}")

    # set_heading(next_station_bearing, turnfn=turn50)

    if not ismine(station_code):
        current_time_taken = R.time() - start_claim_time
        if current_time_taken < 1.999:
            print(
                f"Only took {current_time_taken} so far - Sleeping for {2-current_time_taken}... waiting for time to claim")
            stop(2 - current_time_taken)

        stop_claim_time = R.time()
        print(
            f"Completing claim of {station_code} at time {stop_claim_time} taking {stop_claim_time-start_claim_time}s")
        R.radio.complete_territory_claim()


# The very first move is hard-coded
if zone0:
    set_power(100, 5)
else:
    set_power(5, 100)
R.sleep(0.45)
move(100, 1)

stations = [
    StationCode.OX,
    StationCode.TS,
    StationCode.VB,
    StationCode.BG,
    StationCode.PL,
    StationCode.BE,
    StationCode.HA,
    StationCode.SZ,
    StationCode.BN,
    StationCode.SW,
    StationCode.HV,
    StationCode.PO,
    StationCode.YL,
    StationCode.SF,
    StationCode.YT,
    StationCode.FL,
    StationCode.EY,
    StationCode.PN,
    StationCode.TH,
    StationCode.BG,
    StationCode.VB,
    StationCode.BE,
    StationCode.HA,
    StationCode.SZ,
    StationCode.BN,
]

prev_station_code = mirror_station(stations[0])
for i in range(0, len(stations)):
    station_code = mirror_station(stations[i])
    next_station_code = mirror_station(stations[(i+1) % len(stations)])
    go_to_station(station_code, prev_station_code)
    stop()

    claim_station(station_code, next_station_code)
    prev_station_code = station_code
