import random

from sr.robot import *
R = Robot()

leftSpeed = 70
rightSpeed = 70
turnSpeed = 20
counterReact = turnSpeed / 2

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

while (True):
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