# Capturing a tower
 - How close can you be to capture?
 - What is the signal strength?

To test this I will place the robot exactly by modifying Arena.wbt to shift the robot to start exactly where I want it to start.

Modify line 34:

from

    DEF ROBOT-1 SRRobot {
      translation 0 0 7
      rotation 0 1 0 0

Change _X_, _Y_, angle in _Radians_ to change the start position

    DEF ROBOT-1 SRRobot {
      translation Y 0 X
      rotation 0 1 0 Radians

where 0,0 is the centre, X is positive to the right, Y is positive up

    ---> +X
    |
    v
    -Y

This is still inside the Circle - and Captures:

    DEF ROBOT-1 SRRobot {
      translation -2.5 0 6.6
      rotation 0 1 0 1.5708

     [BN] - bearing -5.45  distance - 0.46   strength - 4.28


This doesn't capture

    DEF ROBOT-1 SRRobot {
      translation -2.4 0 6.6
      rotation 0 1 0 1.5708

    [BN] - bearing -5.45  distance - 0.56   strength - 2.95

-2.45 doesn't capture

    [BN] - bearing -5.45  distance - 0.51   strength - 3.52

-2.46 doesn't capture

    [BN] - bearing -5.45  distance - 0.50   strength - 3.66

-2.47 doesn't capture

    [BN] - bearing -2.92  distance - 0.49   strength - 3.72

-2.48 doesn't capture

    [BN] - bearing -2.92  distance - 0.49   strength - 3.72

-2.49 doesn't capture

    [BN] - bearing -5.45  distance - 0.47   strength - 4.11

-2.495 does capture

    1| [BN] - bearing -5.45  distance - 0.46   strength - 4.19
    BN CLAIMED BY ZONE_1 AT 4.072s

> strength > 4.2 means you can capture