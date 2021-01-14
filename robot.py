import random

from sr.robot import *
R = Robot()

leftSpeed = 80
rightSpeed = 80

R.motors[0].m0.power = 50
R.motors[0].m1.power = 60
R.sleep(3)
R.motors[0].m0.power = 0
R.motors[0].m1.power = 0

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
    
    if(greatestSignal > 1):
        R.motors[0].m0.power = leftSpeed / (greatestSignal * 3 ) + 10
        R.motors[0].m1.power = rightSpeed / (greatestSignal * 3 ) + 10
    
    if R.ruggeduinos[0].digital_read(2):
        print(greatestSignal)
        if(greatestSignal > 30):
            R.sleep(1)
        R.motors[0].m0.power = random.randint(-80, -20)
        R.motors[0].m1.power = random.randint(20, 80)
        R.sleep(1)
   
 
    R.sleep(0.01)
    
