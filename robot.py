from sr.robot import *
R = Robot()

# SR2021 Microgames | Team SPA Solutions

# 0. Join the Discord chat!
#   By now, all team members should be in the Discord chat!

# 1. Getting Started
#   - Install webots from: https://cyberbotics.com/#download
#   - Clone our team repo: https://github.com/Paladins-of-St-Pauls/StudentRobotics

# 2. Hello World
#   Print out a 'Secret Message!'
print(f"Secret Code: H3"+str(35%12)+f"0 W{0}{chr(82)}LD")

# 3. Motor Movement
#   Drive forawrd for 4 seconds, then drive backwards for 2 seconds.
R.motors[0].m0.power = 10
R.motors[0].m1.power = 10
R.sleep(4)
R.motors[0].m0.power = -10
R.motors[0].m1.power = -10
R.sleep(2)
R.motors[0].m0.power = 0
R.motors[0].m1.power = 0

R.sleep(1)

# 4. Microswitches & 5. Light up the Sky
#   Drive until hitting an obstacle with the red LED on, at which point, reverse with the green LED on and then stop.

R.motors[0].m0.power = 30
R.motors[0].m1.power = 10

R.ruggeduinos[0].digital_write(9, True)

while R.ruggeduinos[0].digital_read(2) == False:    
    R.sleep(0.01)

R.motors[0].m0.power = 0
R.motors[0].m1.power = 0

R.ruggeduinos[0].digital_write(9, False)
R.sleep(0.5)
R.ruggeduinos[0].digital_write(8, True)

R.sleep(0.5)

R.motors[0].m0.power = -20
R.motors[0].m1.power = -20

R.sleep(2)

# 6. Distance Sensors
#   Continue reversing until 30cm away from nearest object (Red LED while reversing, green LED once stopped)

R.ruggeduinos[0].digital_write(8, False)
R.sleep(0.5)
R.ruggeduinos[0].digital_write(9, True)

while R.ruggeduinos[0].analogue_read(4) > 0.3:
    R.sleep(0.01)

R.motors[0].m0.power = 0
R.motors[0].m1.power = 0

R.ruggeduinos[0].digital_write(9, False)
R.sleep(0.5)
R.ruggeduinos[0].digital_write(8, True)