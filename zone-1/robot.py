from sr.robot import *
import math
from collections import defaultdict, deque
import numpy
from enum import IntEnum
import random
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

station_zone0_depends_dict = {
    StationCode.OX: [],
    StationCode.TS: [StationCode.OX],
    StationCode.VB: [StationCode.BG, StationCode.OX, StationCode.EY],
    StationCode.BG: [],
    StationCode.PN: [],
    StationCode.TH: [StationCode.PN],
    StationCode.EY: [StationCode.PN, StationCode.VB],
    StationCode.PL: [StationCode.VB, StationCode.SZ],
    StationCode.BE: [StationCode.VB, StationCode.SZ],
    StationCode.HA: [StationCode.BE],
    StationCode.YT: [StationCode.HA],
    StationCode.FL: [StationCode.EY, StationCode.PO],
    StationCode.SZ: [StationCode.BE, StationCode.PL, StationCode.PO],
    StationCode.PO: [StationCode.FL, StationCode.SZ],
    StationCode.SW: [StationCode.BN],
    StationCode.BN: [StationCode.SZ],
    StationCode.HV: [StationCode.SZ],
    StationCode.YL: [StationCode.PO],
    StationCode.SF: [StationCode.YL]
}

station_zone1_depends_dict = {
    StationCode.BN: [],
    StationCode.SW: [StationCode.BN],
    StationCode.SZ: [StationCode.HV, StationCode.BN, StationCode.PO],
    StationCode.HV: [],
    StationCode.YL: [],
    StationCode.SF: [StationCode.YL],
    StationCode.PO: [StationCode.YL, StationCode.SZ],
    StationCode.PL: [StationCode.SZ, StationCode.VB],
    StationCode.BE: [StationCode.SZ, StationCode.VB],
    StationCode.HA: [StationCode.BE],
    StationCode.YT: [StationCode.HA],
    StationCode.FL: [StationCode.PO, StationCode.EY],
    StationCode.VB: [StationCode.BE, StationCode.PL, StationCode.EY],
    StationCode.EY: [StationCode.FL, StationCode.VB],
    StationCode.TS: [StationCode.OX],
    StationCode.OX: [StationCode.VB],
    StationCode.BG: [StationCode.VB],
    StationCode.PN: [StationCode.EY],
    StationCode.TH: [StationCode.PN]
}


def mirror_station(stationcode):
    return stationcode if zone0 else station_mirror_dict[stationcode]


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


def read_distance_sensor(sensor_enum):
    return R.ruggeduinos[0].analogue_read(sensor_enum)


def set_power(left, right):
    m_left.power = left
    m_right.power = right


def get_heading(n=5):
    heading = 0
    for _ in range(0, n):
        heading += R.compass.get_heading()
    return heading/n * (360/math.tau)


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


tx_status = defaultdict(dict)
for station_code in StationCode:
    tx_status[station_code]['tx'] = None
    tx_status[station_code]['strength'] = None
    tx_status[station_code]['bearing'] = None
    tx_status[station_code]['distance'] = None
    tx_status[station_code]['owner'] = None

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
    for stationCode in tx_status['latest']:
        bearing = tx_status[stationCode]['bearing']
        distance = tx_status[stationCode]['distance']
        angle = (180 + heading + bearing) % 360
        # print(f"{station_code} Bearing: {bearing:.0f} Distance {distance:.2f}")
        # print(f"{station_code} Heading+Bearing: {heading+bearing:.0f} Distance {distance:.2f}")
        # print(f"Robot Pos relative to {station_code} is {angle:.0f} degrees {distance:.2f}m")
        x = station_pos_dict[stationCode][0] + \
            math.sin(angle/360*math.tau)*distance
        y = station_pos_dict[stationCode][1] - \
            math.cos(angle/360*math.tau)*distance
        # print(f"Robot at {x:.2f}, {y:.2f}")
        xs.append(x)
        ys.append(y)
        weights.append(1.0/(distance + 0.1))
    if len(xs) < 1:
        return
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
        stationcode = tx.target_info.station_code
        tx_status['latest'].append(stationcode)
        # copy the full struct
        tx_status[stationcode]['tx'] = tx
        # and the individual values
        tx_status[stationcode]['strength'] = tx.signal_strength
        tx_status[stationcode]['bearing'] = tx.bearing * 360 / math.tau
        tx_status[stationcode]['owner'] = tx.target_info.owned_by
        tx_status[stationcode]['distance'] = signal_strength_to_distance(
            tx.signal_strength)
        print(f"[{stationcode}] - bearing {tx_status[stationcode]['bearing']:.2f}  distance - {tx_status[stationcode]['distance']:.2f}   strength - {tx_status[stationcode]['strength']:.2f}  ownedby {tx.target_info.owned_by}")
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
    scale = 1.0 - math.fabs(bearing)/90
    if bearing > 0:
        set_power(power, scale*power)
        print(f"move_to_bearing: power:{power:.0f},{scale*power:.0f} time:{sleep_time:0.2f} bearing:{bearing:.1f}")
    else:
        set_power(scale*power, power)
        print(f"move_to_bearing: power:{power:.0f},{scale * power:.0f} time:{sleep_time:0.2f} bearing:{bearing:.1f}")
    R.sleep(sleep_time)


def mirror(degrees):
    return degrees if zone0 else (360 - degrees) % 360


def get_distance(p1, p2):
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    return math.sqrt(dx*dx + dy*dy)


def get_station_distance(stationcode):
    return get_distance(last_robot_pos, station_pos_dict[stationcode])


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


def get_bearing_distance_strength(stationcode):
    if not stationcode in tx_status['latest']:
        print(
            f"Can't see {stationcode} using last known robot pos {last_robot_pos} and location of station {stationcode} {station_pos_dict[stationcode]}")
        # We can't see the station but we can estimate the direction to go based
        # on our last known position and the location of the tower
        bearing = get_bearing(last_robot_pos, station_pos_dict[stationcode])
        distance = get_distance(last_robot_pos, station_pos_dict[stationcode])
        strength = 0
    else:
        bearing = tx_status[stationcode]['bearing']
        strength = tx_status[stationcode]['strength']
        distance = tx_status[stationcode]['distance']
    return bearing, distance, strength


def get_station_depends(stationcode):
    # The stationcode passed in here is the actual stationcode, but the dependency
    # map is for zone0, we'll need to flip for zone1
    depends_dict = station_zone0_depends_dict if zone0 else station_zone1_depends_dict
    return depends_dict[stationcode]


def is_station_claimable(stationcode):
    # Returns False if we definitely cannot claim it, we might return True here
    # even though we can't claim it if we have been updated properly.
    depends = get_station_depends(stationcode)

    # If there are no dependencies then the station is attached to home base
    # and always claimable
    if not depends:
        # Empty - no dependencies
        return True

    # If any of the dependencies are owned by us then we can claim
    for s in depends:
        if ismine(s):
            return True

    print(f"Station {stationcode} is NOT CLAIMABLE, dependencies {depends}")

    # We cannot claim this yet
    return False


stations_claimed = []


def reclaim_dependents(stationcode, nextstation):
    print(f"Need to reclaim dependents for {stationcode}")
    depends = get_station_depends(stationcode)
    if depends:
        if any(is_station_claimable(s) for s in depends):
            for station in depends:
                if is_station_claimable(station):
                    go_to_station(station, stationcode)
                    claim_station(station, stationcode)

        else:
            station = depends[0]
            reclaim_dependents(station, stationcode)
        go_to_station(stationcode, station)
        claim_station(stationcode, nextstation)



def avoid_centre_wall_problems(stationcode):
    # The centre wall is only a problem if the robot and the target are on other sides
    # of the wall within +/- 3.5 in x and +/- 0.5 in y
    station_pos = station_pos_dict[stationcode]
    if (station_pos[1] > 0 and last_robot_pos[1] < 0) or (station_pos[1] < 0 and last_robot_pos[1] > 0):
        # the robot and the target are on opposite sides
        if last_robot_pos[0] > -3.3 and last_robot_pos[0] < 3.3:
            if last_robot_pos[1] > -0.5 and last_robot_pos[1] < 0.5:
                # We need to add in some way points
                waypoint1 = [math.copysign(3.7, last_robot_pos[0]), math.copysign(0.5, last_robot_pos[1])]
                waypoint2 = [math.copysign(3.7, last_robot_pos[0]), math.copysign(0.5, -last_robot_pos[1])]
                print(f"CENTRE WALL PROBLEM - robot_pos {last_robot_pos}  -> {stationcode} {station_pos}")
                print(f"CENTRE WALL PROBLEM - waypoint1 {waypoint1}  -> waypoint2 {waypoint2}")
                waypoint1_bearing = get_bearing(last_robot_pos, waypoint1)
                set_heading(waypoint1_bearing)
                go_to_waypoint(waypoint1, exit_distance=0.2)
                go_to_waypoint(waypoint2, exit_distance=0.2)


def go_to_station_exceptions(stationcode, prev_stationcode):
    def matches_station(prev, current):
        return prev_stationcode == mirror_station(prev) and stationcode == mirror_station(current)

    if matches_station(StationCode.BG, StationCode.PL):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        # extra careful to avoid the obstacle
        go_to_waypoint(mirror_coords([-3.4, 0.65]))
        stop()

    if matches_station(StationCode.SW, StationCode.HV):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_stationcode}------>{stationcode}##############################")
            go_to_waypoint(mirror_coords([3.1, 1.1]))
            stop()

    if matches_station(StationCode.BG, StationCode.OX):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_stationcode}------>{stationcode}##############################")
            go_to_waypoint(mirror_coords([-2.5, 1.2]))
            stop()

    if matches_station(StationCode.OX, StationCode.BG):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_stationcode}------>{stationcode}##############################")
            go_to_waypoint(mirror_coords([-2.5, 1.2]))
            stop()

    if matches_station(StationCode.BN, StationCode.SZ):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_stationcode}------>{stationcode}##############################")
            go_to_waypoint(mirror_coords([2.5, 1.2]))
            stop()

    if matches_station(StationCode.SZ, StationCode.BN):
        # If game time is less than a minute the direct route is blocked by a wall
        if R.time() < 60:
            print(f"###########{prev_stationcode}------>{stationcode}##############################")
            go_to_waypoint(mirror_coords([2.5, 1.2]))
            stop()

    if matches_station(StationCode.SZ, StationCode.BN):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        go_to_waypoint(mirror_coords([2.4, 1.7]), exit_distance=0.5)

    if matches_station(StationCode.VB, StationCode.BG):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        go_to_waypoint(mirror_coords([-3.6, 0.8]), exit_distance=0.5)

    if matches_station(StationCode.OX, StationCode.TS):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        go_to_waypoint(mirror_coords([-4.7, 3.0]), exit_distance=0.5)

    if matches_station(StationCode.SF, StationCode.YT):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        go_to_waypoint(mirror_coords([3.8, -2.2]), exit_distance=0.5)

    if matches_station(StationCode.BE, StationCode.HA):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        # Hug around the node until we are past it
        # Depends which way we are facing, if we are heading east
        if get_heading() < 180:
            left_power = 30
            right_power = 100
        else:
            left_power = 100
            right_power = 30

        for i in range(0, 10):
            set_power(left_power, right_power)
            R.sleep(0.1)
            sweep()
            if last_robot_pos[1] < 1.4:
                break

    if matches_station(StationCode.HV, StationCode.PO):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        # Here we need to be careful of the centre wall
        # Hug around the node
        for i in range(0, 10):
            set_power(30, 100)
            R.sleep(0.1)
            sweep()
            if last_robot_pos[1] < -0.10:
                break

    if matches_station(StationCode.BG, StationCode.VB):
        print(f"###########{prev_stationcode}------>{stationcode}##############################")
        # Here we need to be careful of the centre wall
        # Hug around the node
        for i in range(0, 10):
            set_power(30, 100)
            R.sleep(0.1)
            sweep()
            if last_robot_pos[1] > -0.2:
                break


def rotate_to_target_bearing(target_heading, close_enough_angle=4, start_claim_time=None):
    current_heading = get_heading()
    diff_heading = diff_bearing(target_heading, current_heading)
    max_turn = 90
    if diff_heading > max_turn:
        target_heading = add_bearing(current_heading, max_turn)
    elif diff_heading < -max_turn:
        target_heading = add_bearing(current_heading, -max_turn)

    print(f"Rotating {diff_heading:.0f} to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
    max_iterations = 50
    iterations = 0
    slow_down_angle = 60
    # First time - give it a kick with 100% power
    if math.fabs(diff_heading) > 15:
        power = math.copysign(100, diff_heading)
        print(f"Rotating with power {power:.0f} to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
        set_power(power, -power)
        R.sleep(0.05)           
    current_heading = get_heading()
    diff_heading = diff_bearing(target_heading, current_heading)
    while math.fabs(diff_heading) > close_enough_angle:
        if math.fabs(diff_heading > slow_down_angle):
            power = math.copysign(100, diff_heading)
        else: 
            stop()
            power = math.copysign(min(100, (math.fabs(diff_heading) * 90 / slow_down_angle) + 10), diff_heading)
        print(f"Rotating {diff_heading:.0f} with power {power:.0f} to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
        set_power(power, -power)
        R.sleep(0.03)    
        current_heading = get_heading()
        diff_heading = diff_bearing(target_heading, current_heading)
        # If the claim time has elapsed break the while loop
        if start_claim_time and R.time() - start_claim_time > 1.99:
            print("Exiting turn early, claim time expiring")
            break
        # If we have done too many iterations(possibly stuck while turning) break the while loop
        iterations += 1
        if iterations > max_iterations:
            print("Exiting turn early, we are probably stuck")
            break
    print(f"                                                                       - current heading {current_heading:.0f}")


def go_to_waypoint(point, exit_distance=0.3, slow_down_on_approach=False):
    bearing = get_bearing(last_robot_pos, point)
    distance = get_distance(last_robot_pos, point)
    print(f"GOTO {point}  distance: {distance:.2f} bearing: {bearing:.0f}")
    while distance > exit_distance:
        power = 100 if not slow_down_on_approach or distance > 1.1 else 100 * distance + 10
        move_to_bearing(power, 0.1, bearing)
        sweep()
        bearing = get_bearing(last_robot_pos, point)
        distance = get_distance(last_robot_pos, point)
        print(f"GOTO {point}  distance: {distance:.2f} bearing: {bearing:.0f}")
        if front_bumper() or not_moving():
            if front_bumper():
                print("stuck - front bumper pressed")
            else:
                print("stuck - not moving")
            if distance < 0.5:
                # We are probably close enough to the waypoint to
                # continue
                print(f"Continuing anyway, we ar {distance} from {point}")
                break
            # move back with random powers -50 to -100 so we can get some random turning
            set_power(random.randrange(-100, -50), random.randrange(-100, -50))
            R.sleep(0.3)
            set_heading(bearing)
            sweep()
            bearing = get_bearing(last_robot_pos, point)
            distance = get_distance(last_robot_pos, point)


def go_to_station(stationcode, prev_stationcode):
    if ismine(stationcode) and stationcode in tx_status['latest']:
        stop()
        return
    go_to_station_exceptions(stationcode, prev_stationcode)
    bearing, distance, strength = get_bearing_distance_strength(stationcode)
    print(f"Go to {stationcode} - bearing {bearing:.2f}  distance - {distance:.2f}   strength - {strength:.2f}")
    while strength < 4.2:
        move_to_bearing(100, 0.1, bearing)
        # move(100, 0.2 if strength < 1.5 else 0.1)
        sweep()
        if ismine(stationcode) and stationcode in tx_status['latest']:
            stop()
            return
        bearing, distance, strength = get_bearing_distance_strength(stationcode)
        print(
            f"Go to {stationcode} - bearing {bearing:.2f}  distance - {distance:.2f}   strength - {strength:.2f}")
        if front_bumper() or not_moving():
            if front_bumper():
                print("stuck - front bumper pressed")
            else:
                print("stuck - not moving")
            # move back with random powers -50 to -100 so we can get some random turning
            set_power(random.randrange(-100, -50), random.randrange(-100, -50))
            R.sleep(0.2)
            sweep()
            stop()
            bearing, distance, strength = get_bearing_distance_strength(stationcode)
            heading = get_heading()
            set_heading(heading + bearing)
        if not is_station_claimable(stationcode):
            reclaim_dependents(stationcode, stationcode)
        avoid_centre_wall_problems(stationcode)

    print(f"Arrived at {stationcode}")
    return True


def ismine(stationcode):
    mine = Claimant.ZONE_0 if zone0 else Claimant.ZONE_1
    if stationcode in tx_status and 'owner' in tx_status[stationcode]:
        return tx_status[stationcode]['owner'] == mine
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


def diff_heading_fn(a, b):
    return (a - b) % 360


def add_bearing(a, b):
    return (180 + a + b) % 360 - 180    


def claim_station(stationcode, next_stationcode):
    # It looks like you cannot take more than 2.x seconds claiming
    if ismine(stationcode):
        return
    start_claim_time = R.time()
    print(f"Starting claim of {stationcode}, next_station_code={next_stationcode} at time {start_claim_time}")
    R.radio.begin_territory_claim()

    # Stop and sweep - allow the stop to stabilise our position before we sweep
    stop(0.2)
    sweep()

    # Make sure we back up a bit so that we can turn around the station without colliding with it.
    bearing, distance, strength = get_bearing_distance_strength(stationcode)
    target_distance = 0.22
    while distance < target_distance:
        target_diff =  target_distance - distance
        print(f'Moving Back to {target_distance}, {target_diff:.2f} to go - wait time {R.time()-start_claim_time}')
        move(-10-(target_diff*150), 0.1)
        sweep()
        bearing, distance, strength = get_bearing_distance_strength(stationcode)
        if R.time() - start_claim_time > 1.95:
            break        
    stop()

    # Start to turn towards the next station, But turn at 90 degrees so that we a ready to drive off
    # to the next station without hitting the current one
    next_station_bearing = get_absolute_bearing(last_robot_pos, station_pos_dict[next_stationcode])
    current_station_bearing = get_absolute_bearing(last_robot_pos, station_pos_dict[stationcode])
    diff_station_bearing = diff_bearing(next_station_bearing, current_station_bearing)
    print(f"Difference {diff_station_bearing:.0f} in bearing between {stationcode}({current_station_bearing:.0f}) and {next_stationcode}({next_station_bearing:.0f})")
    if diff_station_bearing > 0:
        target_heading = add_bearing(current_station_bearing, 90)
    else:
        target_heading = add_bearing(current_station_bearing, -90)
    current_heading = get_heading()
    print(f"Rotating to target heading {target_heading:.0f} - current heading {current_heading:.0f}")
    rotate_to_target_bearing(target_heading, close_enough_angle=4, start_claim_time=start_claim_time)
    sweep()

    # If we still have time start rotating around the tower, but only
    # for certain towers
    current_time_taken = R.time() - start_claim_time
    if stationcode in (mirror_station(StationCode.BN),
                       mirror_station(StationCode.BE),
                       mirror_station(StationCode.VB),
                       mirror_station(StationCode.HV),
                       mirror_station(StationCode.PN),
                       mirror_station(StationCode.YL),
                       ):
        max_loops = 4
        while current_time_taken < 1.999 and max_loops > 0:
            set_power(25, 100)
            R.sleep(0.05)
            current_time_taken = R.time() - start_claim_time
            max_loops = max_loops - 1

    current_time_taken = R.time() - start_claim_time
    if current_time_taken < 1.999:
        print(
            f"Only took {current_time_taken} so far - Sleeping for {2-current_time_taken}... waiting for time to claim")
        stop(2 - current_time_taken)

    stop_claim_time = R.time()
    print(
        f"Completing claim of {stationcode} at time {stop_claim_time} taking {stop_claim_time - start_claim_time}s")
    R.radio.complete_territory_claim()
    sweep()
    if ismine(stationcode):
        stations_claimed.append(stationcode)
    else:
        # Check again sometimes it doesn't update in time
        sweep()
        if ismine(stationcode):
            stations_claimed.append(stationcode)
        else:
            if is_station_claimable(stationcode):
                R.radio.claim_territory()
                sweep()
                if ismine(stationcode):
                    stations_claimed.append(stationcode)
                else:
                    # Somethings wrong we need to go back through the dependents
                    reclaim_dependents(stationcode, next_stationcode)
            else:
                reclaim_dependents(stationcode, next_stationcode)


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
    # Second pass
    StationCode.PN,
    StationCode.BG,
    StationCode.OX,
    StationCode.TS,
    StationCode.PL,
    StationCode.VB,
    StationCode.BE,
    StationCode.HA,
    StationCode.SZ,
    StationCode.HV,
    StationCode.BN,
    StationCode.SW,
    StationCode.HV,
    StationCode.YL,
    StationCode.SF,



]

prev_station_code = mirror_station(stations[0])
for i in range(0, len(stations)):
    station_code = mirror_station(stations[i])
    next_station_code = mirror_station(stations[(i+1) % len(stations)])
    go_to_station(station_code, prev_station_code)
    stop()

    claim_station(station_code, next_station_code)
    prev_station_code = station_code

go_to_waypoint(mirror_coords([7, 0]))
set_power(100, 30)
R.sleep(1)
