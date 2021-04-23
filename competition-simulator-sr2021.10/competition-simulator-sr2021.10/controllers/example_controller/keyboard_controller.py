from sr.robot import Robot
from controller import Keyboard

# Any keys still pressed in the following period will be handled again
# leading to repeated claim attempts or printing sensors multiple times
KEYBOARD_SAMPLING_PERIOD = 100
NO_KEY_PRESSED = -1

CONTROLS = {
    "forward": (ord("W"), ord("I")),
    "reverse": (ord("S"), ord("K")),
    "left": (ord("A"), ord("J")),
    "right": (ord("D"), ord("L")),
    "claim": (ord("E"), ord("O")),
    "sense": (ord("Q"), ord("U")),
    "scan": (ord("R"), ord("P")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
}


def print_sensors(robot: Robot) -> None:
    distance_sensor_names = [
        "Front Left",
        "Front Right",
        "Left",
        "Right",
        "Back Left",
        "Back Right",
    ]
    touch_sensor_names = [
        "Front",
        "Rear",
    ]

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for pin, name in enumerate(distance_sensor_names):
        dist = R.ruggeduinos[0].analogue_read(pin)
        print(f"{pin} {name: <12}: {dist:.2f}")

    print("Touch sensor readings:")
    for pin, name in enumerate(touch_sensor_names, 2):
        touching = R.ruggeduinos[0].digital_read(pin)
        print(f"{pin} {name: <6}: {touching}")

    print()


R = Robot()

keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

pending_claims = []

key_forward = CONTROLS["forward"][R.zone]
key_reverse = CONTROLS["reverse"][R.zone]
key_left = CONTROLS["left"][R.zone]
key_right = CONTROLS["right"][R.zone]
key_claim = CONTROLS["claim"][R.zone]
key_sense = CONTROLS["sense"][R.zone]
key_scan = CONTROLS["scan"][R.zone]
key_boost = CONTROLS["boost"][R.zone]

print(
    "Note: you need to click on 3D viewport for keyboard events to be picked "
    "up by webots",
)

while True:
    key = keyboard.getKey()

    boost = False

    left_power = 0
    right_power = 0

    while key != NO_KEY_PRESSED:
        key_ascii = key & 0x7F  # mask out modifier keys
        # note: modifiers are only recorded when pressed before other keys
        key_mod = key & (~0x7F)

        if key_mod == key_boost:
            boost = True

        if key_ascii == key_forward:
            left_power += 50
            right_power += 50

        elif key_ascii == key_reverse:
            left_power += -50
            right_power += -50

        elif key_ascii == key_left:
            left_power -= 25
            right_power += 25

        elif key_ascii == key_right:
            left_power += 25
            right_power -= 25

        elif key_ascii == key_claim:
            R.radio.begin_territory_claim()
            pending_claims.append(R.time() + 2)

        elif key_ascii == key_sense:
            print_sensors(R)

        elif key_ascii == key_scan:
            transmitters = R.radio.sweep()
            print("Found transmitter(s)")

            for transmitter in transmitters:
                print(transmitter)

            print()

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = keyboard.getKey()

    if boost:
        # double power values but constrain to [-100, 100]
        left_power = max(min(left_power * 2, 100), -100)
        right_power = max(min(right_power * 2, 100), -100)

    R.motors[0].m0.power = left_power
    R.motors[0].m1.power = right_power

    current_time = R.time()
    # complete claims after their 2 seconds has lapsed
    for claim_end_time in pending_claims:
        if current_time > claim_end_time:
            R.radio.complete_territory_claim()
            pending_claims.remove(claim_end_time)

    R.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
