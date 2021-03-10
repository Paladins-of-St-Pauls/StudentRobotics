import random
import pprint
import math
from collections import defaultdict,deque

from sr.robot import *
R = Robot(1)


leftSpeed = 70
rightSpeed = 70
turnSpeed = 20
counterReact = turnSpeed * 2

print(R.zone)
if False:
    if(R.zone == 1):
        R.motors[0].m0.power = 56
        R.motors[0].m1.power = 53
        R.sleep(2.5)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.3)
    # R.motors[0].m0.power = -1.1
    # R.motors[0].m1.power = 1.5
    # R.sleep(.85)
    # R.motors[0].m0.power = 0
    # R.motors[0].m1.power = 0
    # R.radio.claim_territory()
    # R.sleep(.1)
        R.motors[0].m0.power = 50
        R.motors[0].m1.power = 50
        R.sleep(2.35)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.1)
        #fix direction
        R.motors[0].m0.power = 1.1
        R.motors[0].m1.power = -1.5
        R.sleep(.85)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.1)
        print ('**BABY DRIVER INTENSIFIES**')
        print ('*BABY DRIVER INTENSIFIES*')
        print ('**BABY DRIVER INTENSIFIES**')
        print ('*BABY DRIVER INTENSIFIES*')
        R.motors[0].m0.power = -94
        R.motors[0].m1.power = -90
        R.sleep(2.4)
        #R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.sleep(.4)
        #R.motors[0].m0.power = -30
        #R.motors[0].m1.power = 30
        #R.sleep(.5)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.sleep(.1)
    else:
        R.motors[0].m0.power = 50
        R.motors[0].m1.power = 56
        R.sleep(2.5)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.1)
        R.motors[0].m0.power = 1.5
        R.motors[0].m1.power = -1.1
        R.sleep(.85)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.1)
        R.motors[0].m0.power = 50
        R.motors[0].m1.power = 50
        R.sleep(2.5)
        #fix direction
        R.motors[0].m0.power = -1.1
        R.motors[0].m1.power = 1.5
        R.sleep(.85)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.radio.claim_territory()
        R.sleep(.1)
        print ('**BABY DRIVER INTENSIFIES**')
        print ('*BABY DRIVER INTENSIFIES*')
        print ('**BABY DRIVER INTENSIFIES**')
        print ('*BABY DRIVER INTENSIFIES*')
        R.motors[0].m0.power = -90
        R.motors[0].m1.power = -94
        R.sleep(2.4)
        R.motors[0].m0.power = 0
        #R.motors[0].m1.power = -24
        R.sleep(.4)
        #R.motors[0].m0.power = 30
        #R.motors[0].m1.power = -30
        #R.sleep(.5)
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.sleep(.1)

last_seen_transmitters=deque(maxlen=3)
def are_we_stuck(transmitters):
    last_seen_transmitters.append(transmitters)

    if len(last_seen_transmitters) < 3:
        return False

    stations=defaultdict(list)
    for transmitters in last_seen_transmitters:
        for tx in transmitters:
            stations[tx.target_info.station_code].append(tx.signal_strength)

    # if the number of items in each list is not the same as the length of the deque then
    # we have a changing number of station codes
    for key,value in stations.items():
        if len(value) < len(last_seen_transmitters):
            return False

    # now check the strengths are all within a certain percentage

    for station_code,strengths in stations.items():
        strength_avg = sum(strengths)/len(strengths)
        if max(strengths)/strength_avg > 1.2:
            return False
        if min(strengths)/strength_avg < 0.8:
            return False
    return True

tx_status = {}
for station_code in StationCode:
    tx_status[station_code] = {}

R.motors[0].m0.power = 5 
R.motors[0].m1.power = 5 
while (True):
    

    greatestSignal = 0
    greatestSignalNotMine = 0
    transmitters = R.radio.sweep()

    pprint.pprint(transmitters)
    if are_we_stuck(transmitters):
        print("WE ARE STUCK")

    

    #  [<Target: info=TargetInfo(station_code=<StationCode.PN: 'PN'>, owned_by=None, locked=False), bearing=-1.6641014529817628, strength=1.5047800429345402>,
    #   <Target: info=TargetInfo(station_code=<StationCode.BG: 'BG'>, owned_by=None, locked=False), bearing=0.6825763859138019, strength=0.5934829139807503>]
    closest_tx = None
    closest_not_mine = None
    for tx in transmitters:
        tx_status[tx.target_info.station_code]['tx'] = tx
        if(tx.signal_strength > greatestSignal):
            closest_tx = tx
            greatestSignal = tx.signal_strength
        if (tx.target_info.owned_by != R.zone):
            if(tx.signal_strength > greatestSignalNotMine):
                closest_not_mine = tx
                greatestSignalNotMine = tx.signal_strength                

    if closest_tx.target_info.owned_by != R.zone:
        R.radio.claim_territory()
    
    robot_bearing = R.compass.get_heading()
    if robot_bearing < 0:
        robot_bearing += 2 * math.pi

    if closest_not_mine:
        tower_bearing = closest_not_mine.bearing
        if tower_bearing < 0:
            tower_bearing += 2 * math.pi

        diff = robot_bearing - tower_bearing
        print(f"diff={diff}")
        left_power =  20 - (50*(math.sin(diff)))
        right_power = 20 + (50*math.sin(diff))
        print(f"left={left_power} , right={right_power}")
        R.motors[0].m0.power = left_power
        R.motors[0].m1.power = right_power
    else:
        R.motors[0].m0.power = leftSpeed + random.randint(-30,30)
        R.motors[0].m1.power = rightSpeed + random.randint(-30,30)





while (True):
    
    greatestSignal = 0
    greatestSignalNotMine = 0
    transmitters = R.radio.sweep()

    pprint.pprint(transmitters)


    #  [<Target: info=TargetInfo(station_code=<StationCode.PN: 'PN'>, owned_by=None, locked=False), bearing=-1.6641014529817628, strength=1.5047800429345402>,
    #   <Target: info=TargetInfo(station_code=<StationCode.BG: 'BG'>, owned_by=None, locked=False), bearing=0.6825763859138019, strength=0.5934829139807503>]
    closest_tx = None
    closest_not_mine = None
    for tx in transmitters:
        tx_status[tx.target_info.station_code]['tx'] = tx
        if(tx.signal_strength > greatestSignal):
            closest_tx = tx
            greatestSignal = tx.signal_strength
        if (tx.target_info.owned_by != R.zone):
            if(tx.signal_strength > greatestSignalNotMine):
                closest_not_mine = tx
                greatestSignalNotMine = tx.signal_strength                

    if closest_tx.target_info.owned_by != R.zone:
        R.radio.claim_territory()
    
    if closest_not_mine:
        R
    else:
        pass

    R.motors[0].m0.power = leftSpeed
    R.motors[0].m1.power = rightSpeed
    
        #change back to 2 if it sucks chris 
    if(greatestSignal > 2):
        #R.motors[0].m0.power = 0
        #R.motors[0].m1.power = 0
        #R.sleep(0.5)
        #R.motors[0].m0.power = -turnSpeed
        #R.motors[0].m1.power = turnSpeed
        #R.sleep(0.5)
        if(R.zone == 1):
            R.motors[0].m0.power = 0
            R.motors[0].m1.power = 0
            R.sleep(0.5)
            R.motors[0].m0.power = turnSpeed
            R.motors[0].m1.power = -turnSpeed
            R.sleep(0.5)
        else:
            R.motors[0].m0.power = 0
            R.motors[0].m1.power = 0
            R.sleep(0.5)
            R.motors[0].m0.power = -turnSpeed
            R.motors[0].m1.power = turnSpeed
            R.sleep(0.5)
    if(greatestSignal > greatestSignal):
        #R.motors[0].m0.power = 0
        #R.motors[0].m1.power = 0
        #R.sleep(0.5)
        #R.motors[0].m0.power = counterReact
        #R.motors[0].m1.power = -counterReact
        #R.sleep(0.5)
        if(R.zone == 1):
            R.motors[0].m0.power = 0
            R.motors[0].m1.power = 0
            R.sleep(0.5)
            R.motors[0].m0.power = -counterReact
            R.motors[0].m1.power = counterReact
            R.sleep(0.5)
        else:
            R.motors[0].m0.power = 0
            R.motors[0].m1.power = 0
            R.sleep(0.5)
            R.motors[0].m0.power = counterReact
            R.motors[0].m1.power = -counterReact

#varied slowdown
    if(greatestSignal > .7):
        #R.motors[0].m0.power = leftSpeed / (greatestSignal * 4 ) + 5
        #R.motors[0].m1.power = rightSpeed / (greatestSignal * 4 ) + 5
        if(R.zone == 1):
            R.motors[0].m1.power = leftSpeed / (greatestSignal * 4 ) + 5
            R.motors[0].m0.power = rightSpeed / (greatestSignal * 4 ) + 5
        else:
            R.motors[0].m0.power = leftSpeed / (greatestSignal * 4 ) + 5
            R.motors[0].m1.power = rightSpeed / (greatestSignal * 4 ) + 5


    #if(greatestSignal > .6):
        #R.motors[0].m0.power = leftSpeed / (greatestSignal * 3.5 )
        #R.motors[0].m1.power = rightSpeed / (greatestSignal * 3.5 )
        if(R.zone == 1):
            R.motors[0].m1.power = leftSpeed / (greatestSignal * 3.5 )
            R.motors[0].m0.power = rightSpeed / (greatestSignal * 3.5 )
        else:
            R.motors[0].m0.power = leftSpeed / (greatestSignal * 3.5 )
            R.motors[0].m1.power = rightSpeed / (greatestSignal * 3.5 )


    if(greatestSignal > .5):
        #R.motors[0].m0.power = leftSpeed / (greatestSignal * 3 )
        #R.motors[0].m1.power = rightSpeed / (greatestSignal * 3 )
        if(R.zone == 1):
            R.motors[0].m1.power = leftSpeed / (greatestSignal * 3 )
            R.motors[0].m0.power = rightSpeed / (greatestSignal * 3 )
        else:
            R.motors[0].m0.power = leftSpeed / (greatestSignal * 3 )
            R.motors[0].m1.power = rightSpeed / (greatestSignal * 3 )

#wall turn around
    if R.ruggeduinos[0].digital_read(2):
        print(greatestSignal)
        if(greatestSignal > 30):
            R.sleep(1)
        
        direction = bool(random.getrandbits(1))
        
        if(R.zone == 1):
            R.motors[0].m0.power = (random.randint(25, 35))
            R.motors[0].m1.power = -(random.randint(25, 35))
        else:
            R.motors[0].m0.power = -(random.randint(25, 35))
            R.motors[0].m1.power = (random.randint(25, 35))
        R.sleep(1)
   
 
    R.sleep(0.01)