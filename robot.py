from sr.robot import *
import statistics
import math
from collections import defaultdict,deque
import random
import pprint
import math
from collections import defaultdict,deque

R = Robot()

m_left = R.motors[0].m0
m_right = R.motors[0].m1
leftSpeed = 70
rightSpeed = 70
turnSpeed = 20
counterReact = turnSpeed * 2

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

def drive(power, distance):
    per_distance = 2
    sleep_time = math.fabs(distance/per_distance)
    p = math.copysign(power,distance)
    print(f"MOVE power[{p}] sleep[{sleep_time}]")
    set_power(p,p)
    R.sleep(sleep_time)

def move(power, distance):
    if R.ruggeduinos[0].digital_read(2) == False:
        drive(power,distance)

#CHANGED FROM 0.5 TO 1 ~chris
def stop(sleep_time=1):
    set_power(0,0)
    R.sleep(sleep_time)
    
    
    
def getout():
    print("RUNNNN")
    print("RUNNNN")
    print("RUNNNN")
    print("RUNNNN")
    
def killme():
    print("helprobot")
    print("helprobot")
    print("helprobot")
    print("helprobot")
    print("helprobot")
    
    
    

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

def turnXX(degrees, speed, b, c):
    t = (math.fabs(degrees) - b) / c
    p = math.copysign(25,degrees)
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

if(R.zone == 0):
    # First part by dead-reckoning
    #print("null")
    
   # getout()
    killme()
    print(f"heading = {get_heading(1000)}")
    move(75,1.4)
    stop()
    print(f"heading = {get_heading(1000)}")
    turn(-40)
    stop()
    print(f"heading before correction = {get_heading(1000)}")
    correct_heading(113)
    print(f"heading = {get_heading(1000)}")
    move(75,2.2)
    stop(1.0)
    correct_heading(113)
    R.radio.claim_territory()
    print(f"heading = {get_heading(1000)}")
    move(100,2.6)
    stop(1.5)
    print("1")
    correct_heading(116)
    R.radio.claim_territory()
    print(f"heading = {get_heading(1000)}")
    move(100,-5.3)
    print(f"heading = {get_heading(1000)}")
    stop(1.5)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    move(100, 3)
   # getout()

    print("suspect")
    turn100(100)
    stop()

    print(f"heading = {get_heading(1000)}")
    #move(75,2)
    print(f"heading = {get_heading(1000)}")
    correct_heading(150)
    R.radio.claim_territory()

    stop()

    #move(75,2)
    move(75,3.7)
    print("2")
    R.radio.claim_territory()
    correct_heading(170)
   # print('FOR FUTURE REFERENCES, THATS A BASKET HOLDER, NOT A BASKET')
   # print('FOR FUTURE REFERENCES, THATS A BASKET HOLDER, NOT A BASKET')
    move(50,0.5)
    #R.radio.claim_territory()

   

    stop()
    #BG
    #R.radio.claim_territory()

    #move(75,3.5)
    R.radio.claim_territory()
    correct_heading(170)
    stop()
    #OX
    #R.radio.claim_territory()
    #stop()
    correct_heading(106)
    m_left.power=-60
    m_right.power=-40
    R.sleep(0.7)
    stop()
    move(75,1)
    correct_heading(60)
    move(75,2.2)
    stop()
    #TS
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    move(20,-0.4)
    correct_heading(133)
    # stop()
    move(75,4.5)
    stop()
    stop()
    #VB
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    correct_heading(75)
    move(75,5)
    stop()
    #SZ
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()
    m_left.power=-40
    m_right.power=-60
    R.sleep(1)
    stop()
    correct_heading(180)
    move(75,-4)
    stop()
    #BE
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
else:
    # First part by dead-reckoning
    #print("null")
    
   # getout()
    
    print(f"heading = {get_heading(1000)}")
    move(75,1.4)
    stop()
    print(f"heading = {get_heading(1000)}")
    turn(30)
    stop()
    print(f"heading before correction = {get_heading(1000)}")
    correct_heading(235)
    print(f"heading = {get_heading(1000)}")
    move(75,2.2)
    stop(1.0)
    correct_heading(235)
    R.radio.claim_territory()
    print(f"heading = {get_heading(1000)}")
    move(100,2.6)
    stop(1.5)
    print("1")
    correct_heading(240)
    R.radio.claim_territory()
    print(f"heading = {get_heading(1000)}")
    move(100,-5.3)
    print(f"heading = {get_heading(1000)}")
    stop(1.5)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    correct_heading(180)
    move(100, 3)
   # getout()

     # First part by dead-reckoning
    turn100(-93)
    stop()

    print(f"heading = {get_heading(1000)}")
    #move(75,1)
    print("tgatghjjhdgetshjgjdtfghs")
    print("tgatghjjhdgetshjgjdtfghs")
    print("tgatghjjhdgetshjgjdtfghs")
   # stop()

    print(f"heading = {get_heading(1000)}")
    correct_heading(200)
    R.radio.claim_territory()

   # move(75,2)
 #   correct_heading(190)
    #move(50,0.5)
    stop()
    stop()



    #HV

    move(75,3.5)
    correct_heading(190)
    stop()
    #BN
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    correct_heading(260)
    m_left.power=-40
    m_right.power=-60
    R.sleep(0.7)
    stop()
    move(75,1)
    correct_heading(300)
    move(75,2.7)
    stop()
    #SW
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    move(20,-0.4)
    correct_heading(230)
    # stop()
    move(75,4.7)
    stop()
    stop()
    #SZ
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    correct_heading(285)
    move(75,5)
    stop()
    #VB
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    m_left.power=-60
    m_right.power=-40
    R.sleep(1)
    stop()
    correct_heading(180)
    move(75,-4)
    stop()
    #BE
    if R.ruggeduinos[0].digital_read(2) == False:
        R.radio.claim_territory()
        stop()   
    
    
    
    
    
while (True):
    R.ruggeduinos[0].digital_write(4, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(4, False)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(7, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(7, False)
    R.sleep(.1)
    
    R.ruggeduinos[0].digital_write(5, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(5, False)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(8, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(8, False)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(6, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(6, False)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(9, True)
    R.sleep(.1)

    R.ruggeduinos[0].digital_write(9, False)
    R.sleep(.1)

    R.sleep(0.01)
    R.radio.claim_territory()
    greatestSignal = 0
    transmitters = R.radio.sweep()
    for tx in transmitters:
        if(tx.signal_strength > greatestSignal):
            if(tx.target_info.owned_by != R.zone):
                greatestSignal = tx.signal_strength

    R.motors[0].m0.power = leftSpeed
    R.motors[0].m1.power = rightSpeed
    
    if(greatestSignal > 2):
        
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.sleep(0.5)
        R.motors[0].m0.power = -turnSpeed
        R.motors[0].m1.power = turnSpeed
        R.sleep(0.5)
    if(greatestSignal > greatestSignal):
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
        R.sleep(0.5)
        R.motors[0].m0.power = counterReact
        R.motors[0].m1.power = -counterReact
        R.sleep(0.5)

#varied slowdown
    if(greatestSignal > .7):
        R.motors[0].m0.power = leftSpeed / (greatestSignal * 4 ) + 5
        R.motors[0].m1.power = rightSpeed / (greatestSignal * 4 ) + 5


    if(greatestSignal > .6):
        R.motors[0].m0.power = leftSpeed / (greatestSignal * 3.5 )
        R.motors[0].m1.power = rightSpeed / (greatestSignal * 3.5 )


    if(greatestSignal > .5):
        R.motors[0].m0.power = leftSpeed / (greatestSignal * 3 )
        R.motors[0].m1.power = rightSpeed / (greatestSignal * 3 )

#wall turn around
    if R.ruggeduinos[0].digital_read(2):
        print(greatestSignal)
        if(greatestSignal > 30):
            R.sleep(1)
        
        direction = bool(random.getrandbits(1))
        
        if(direction):
            R.motors[0].m0.power = -(random.randint(25, 35))
            R.motors[0].m1.power = (random.randint(25, 35))
        else:
            R.motors[0].m0.power = (random.randint(25, 35))
            R.motors[0].m1.power = -(random.randint(25, 35))
        R.sleep(1)
   
 
    R.sleep(0.01)