import enum
import struct
from typing import Dict, Tuple

# Webots specific library
from controller import Emitter, Receiver, Supervisor  # isort:skip

# Updating? Update `Arena.wbt` too
ZONE_COLOURS = ((1, 0, 1), (1, 1, 0))

RECEIVE_TICKS = 1

# Updating? Update radio.py too.
BROADCASTS_PER_SECOND = 10


# Updating? Update radio.py too.
class Claimant(enum.IntEnum):
    UNCLAIMED = -1
    ZONE_0 = 0
    ZONE_1 = 1


# Updating? Update radio.py too.
class StationCode(str, enum.Enum):
    PN = 'PN'
    EY = 'EY'
    BE = 'BE'
    PO = 'PO'
    YL = 'YL'
    BG = 'BG'
    TS = 'TS'
    OX = 'OX'
    VB = 'VB'
    SZ = 'SZ'
    SW = 'SW'
    BN = 'BN'
    HV = 'HV'


class TerritoryController:

    _emitters: Dict[StationCode, Emitter]
    _receivers: Dict[StationCode, Receiver]

    def __init__(self) -> None:
        self._robot = Supervisor()
        self._station_statuses: Dict[StationCode, Claimant] = {
            code: Claimant.UNCLAIMED for code in StationCode
        }
        self._claim_starts: Dict[Tuple[StationCode, Claimant], float] = {}

    def get_claimant(
        self,
        station_code: StationCode,
    ) -> Claimant:
        return self._station_statuses[station_code]

    def setup(self) -> None:
        self._emitters = {station_code: self._robot.getEmitter(station_code + "Emitter")
                          for station_code in StationCode}

        self._receivers = {station_code: self._robot.getReceiver(station_code + "Receiver")
                           for station_code in StationCode}
        territory_controller.enable_receivers()

    def enable_receivers(self) -> None:
        for receiver in self._receivers.values():
            receiver.enable(RECEIVE_TICKS)

    def _log_territory_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        # TODO add better logging so we can score
        print(f"{station_code} CLAIMED BY {claimed_by} AT {claim_time}s")  # noqa:T001

    def begin_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        self._claim_starts[station_code, claimed_by] = claim_time

    def has_begun_claim_in_time_window(
        self,
        station_code: StationCode,
        claimant: Claimant,
        current_time: float,
    ) -> bool:
        try:
            start_time = self._claim_starts[station_code, claimant]
        except KeyError:
            return False
        time_delta = current_time - start_time
        return 1.8 <= time_delta <= 2.1

    def claim_territory(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        if self.get_claimant(station_code) == claimed_by:
            # This territory is already claimed by this claimant.
            return

        new_colour = ZONE_COLOURS[claimed_by]
        self._robot.getFromDef(station_code).getField("zoneColour").setSFColor(
            list(new_colour),
        )

        self._log_territory_claim(station_code, claimed_by, self._robot.getTime())
        self._station_statuses[station_code] = claimed_by

    def process_packet(
        self,
        station_code: StationCode,
        packet: bytes,
        receive_time: float,
    ) -> None:
        try:
            robot_id, is_conclude = struct.unpack("!BB", packet)
            if is_conclude:
                if self.has_begun_claim_in_time_window(
                    station_code,
                    robot_id,
                    receive_time,
                ):
                    self.claim_territory(
                        station_code,
                        robot_id,
                        receive_time,
                    )
            else:
                self.begin_claim(
                    station_code,
                    robot_id,
                    receive_time,
                )
        except ValueError:
            print(  # noqa:T001
                f"Received malformed packet at {receive_time} on {station_code}: {packet!r}",
            )

    def receive_territory(self, station_code: StationCode, receiver: Receiver) -> None:
        simulation_time = self._robot.getTime()

        while receiver.getQueueLength():
            try:
                data = receiver.getData()
                self.process_packet(station_code, data, simulation_time)
            finally:
                # Always advance to the next packet in queue: if there has been an exception,
                # it is safer to advance to the next.
                receiver.nextPacket()

    def receive_robot_captures(self) -> None:
        for station_code, receiver in self._receivers.items():
            self.receive_territory(station_code, receiver)

    def transmit_pulses(self) -> None:
        for station_code, emitter in self._emitters.items():
            emitter.send(struct.pack("!2sb", station_code.encode('ASCII'),
                         int(self.get_claimant(station_code))))

    def main(self) -> None:
        self.setup()
        timestep = self._robot.getBasicTimeStep()
        steps_per_broadcast = (1 / BROADCASTS_PER_SECOND) / (timestep / 1000)
        counter = 0
        while True:
            counter += 1
            self.receive_robot_captures()
            if (counter > steps_per_broadcast):
                self.transmit_pulses()
                counter = 0
            self._robot.step(int(self._robot.getBasicTimeStep()))


if __name__ == "__main__":
    territory_controller = TerritoryController()
    territory_controller.main()
