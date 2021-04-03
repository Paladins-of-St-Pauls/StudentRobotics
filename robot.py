from sr.robot import *
import statistics
import math
from collections import defaultdict,deque
import numpy
from sklearn.metrics import r2_score
from enum import IntEnum
from pprint import pprint

debug_active = True

class LED(IntEnum):
    RIGHT_RED   = 4
    RIGHT_GREEN = 5
    RIGHT_BLUE  = 6
    LEFT_BLUE   = 7
    LEFT_GREEN  = 8
    LEFT_RED    = 9

class SENSOR(IntEnum):
    FRONT_LEFT  = 0
    FRONT_RIGHT = 1
    LEFT        = 2
    RIGHT       = 3
    BACK_LEFT   = 4
    BACK_RIGHT  = 5    

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
        
class MotorController:
    def __init__(self, robot, l_motor, r_motor) -> None:     
        self.robot = robot   
        self.motor_left = l_motor
        self.motor_right = r_motor

    def __set_motor_power(self, left_power, right_power) -> None:
        self.motor_left.power = left_power
        self.motor_right.power = right_power

    def drive(self, power) -> None:
        self.__set_motor_power(power, power)

    def stop(self) -> None:
        self.__set_motor_power(0,0)

    def turn(self, degrees, power, b, c) -> float:
        t = (math.fabs(degrees) - b) / c
        p = math.copysign(power,degrees)
        #print(f"TURN power[{power}] sleep[{t}]")
        self.__set_motor_power(power,-power)
        self.robot.sleep(t)    
        return t    
        
class SensorController:
    def __init__(self, robot, station_codes) -> None:
        self.robot = robot        
        self.tx_status = defaultdict(dict)
        for station_code in station_codes:
            self.tx_status[station_code]['tx'] = None
            self.tx_status[station_code]['strength'] = None
            self.tx_status[station_code]['bearing'] = None

    def get_distance(self, sensor) -> float:
        return self.robot.ruggeduinos[0].analogue_read(sensor)

    def set_led(self, led, state) -> None:
        self.robot.ruggeduinos[0].digital_write(led, state)

    def get_compass_heading_raw(self) -> float:
        return self.robot.compass.get_heading()

    def get_compass_heading(self,num_readings=5) -> float:
        heading = 0
        for i in range(0,num_readings):
            heading += self.robot.compass.get_heading()
        return heading/num_readings * (360/math.tau)

    def radio_sweep(self, tx_data):
        transmitters = self.robot.radio.sweep()
        # Keep the latest sweep code in 'latest'
        self.tx_status['latest'] = []
        for tx in transmitters:
            station_code = tx.target_info.station_code
            self.tx_status['latest'].append(station_code)
            # copy the full struct
            self.tx_status[station_code]['tx'] = tx
            # and the individual values
            self.tx_status[station_code]['strength'] = tx.signal_strength
            self.tx_status[station_code]['bearing'] = tx.bearing * 360 / math.tau
            self.tx_status[station_code]['owner'] = tx.target_info.owned_by
            self.tx_status[station_code]['distance'] = signal_strength_to_distance(tx.signal_strength)
            #print(f"[{station_code}] - bearing {tx_status[station_code]['bearing']:.2f}  distance - {tx_status[station_code]['distance']:.2f}   strength - {tx_status[station_code]['strength']:.2f}") if debug_active else \
    
    def get_tx_status() -> dict:
        return self.tx_status

class Pose:
    def __init__(self, robot, sc, init_x, init_y):
        self.location = numpy.array([init_x, init_y])
        self.robot = robot
        self.sensor_controller = sc
        self.heading = init_heading

    def set_location(self, x, y):
        self.location = numpy.array([x, y])

    def estimate_location(self):
        xs = []
        ys = []
        weights = []
        tx_status = self.sensor_controller.get_tx_status
        for station_code in tx_status['latest']:
            bearing = tx_status[station_code]['bearing']
            distance = tx_status[station_code]['distance']
            angle = (180 + sc.get_compass_heading + bearing)%360
            x = station_pos_dict[station_code][0] + math.sin(angle/360*math.tau)*distance
            y = station_pos_dict[station_code][1] - math.cos(angle/360*math.tau)*distance
            xs.append(x)
            ys.append(y)
            weights.append(1.0/(distance + 0.1))
        if len(xs) < 1:
            return
        x = numpy.average(xs)
        y = numpy.average(ys)
        xw = numpy.average(xs,weights=weights)
        yw = numpy.average(ys,weights=weights)
        distance_moved_since_last_update = get_distance(last_robot_pos, [xw,yw])
        set_location(xw, yw)
        last_robot_pos_list.append(distance_moved_since_last_update)

class EnvironmentMapper:
    def __init__(self):
        pass

class WaypointController:
    def __init__(self):
        pass

class PathFinder:
    def __init__(self):
        pass    

class Navigator:
    def __init__(self):
        pass    
            
robot = Robot()
mc = MotorController(robot, robot.motors[0].m0, robot.motors[0].m1)
sc = SensorController(robot, StationCode)