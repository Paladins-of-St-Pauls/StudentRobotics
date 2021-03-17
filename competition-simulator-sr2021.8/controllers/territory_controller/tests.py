import re
import unittest
from typing import Dict, List, Union, Mapping
from pathlib import Path
from unittest.mock import patch

from territory_controller import (
    Claimant,
    ClaimLog,
    StationCode,
    TerritoryRoot,
    TERRITORY_LINKS,
    AttachedTerritories,
    TerritoryController,
    LOCKED_OUT_AFTER_CLAIM,
)

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestAttachedTerritories(unittest.TestCase):
    'Test build_attached_capture_trees/get_attached_territories'

    _zone_0_territories = {
        StationCode.BG,
        StationCode.TS,
        StationCode.OX,
        StationCode.VB,
        StationCode.BE,
        StationCode.SZ,
    }
    _zone_1_territories = {StationCode.PN, StationCode.EY, StationCode.PO, StationCode.YL}
    _zone_1_disconnected = {StationCode.PN, StationCode.EY}

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        # territories BG, TS, OX, VB, BE, SZ owned by zone 0
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory].owner = Claimant.ZONE_0

        # territories PN, EY, PO, YL owned by zone 1
        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory].owner = Claimant.ZONE_1

    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.load_territory_owners(claim_log)
        self.attached_territories = AttachedTerritories(claim_log)
        self.connected_territories = self.attached_territories.build_attached_capture_trees()

    def test_connected_zone_0_territories(self) -> None:
        "test multiple paths and loops don't cause a double entry"

        self.assertEqual(
            self.connected_territories[0],
            self._zone_0_territories,
            'Zone 0 has incorrectly detected connected territories',
        )

    def test_connected_zone_1_territories(self) -> None:
        'test cut-off zones are not included'
        zone_1_attached = {
            station
            for station in self._zone_1_territories
            if station not in self._zone_1_disconnected
        }

        self.assertEqual(
            self.connected_territories[1],
            zone_1_attached,
            'Zone 1 has incorrectly detected connected territories',
        )

    def test_stations_can_capture(self) -> None:
        for station in {StationCode.PN, StationCode.EY, StationCode.SW, StationCode.PO}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                True,
                f'Zone 0 should be able to capture {station}',
            )

        for station in {StationCode.BE, StationCode.SW, StationCode.HV}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                True,
                f'Zone 1 should be able to capture {station}',
            )

    def test_stations_cant_capture(self) -> None:
        for station in {StationCode.YL, StationCode.BN, StationCode.HV}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                False,
                f'Zone 0 should not be able to capture {station}',
            )

        for station in {
            StationCode.PN,
            StationCode.EY,
            StationCode.SZ,
            StationCode.BN,
            StationCode.VB,
        }:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                False,
                f'Zone 1 should not be able to capture {station}',
            )


class TestAdjacentTerritories(unittest.TestCase):
    'Test the AttachedTerritories initialisation of adjacent_zones'

    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.attached_territories = AttachedTerritories(claim_log)

    def test_all_links_in_set(self) -> None:
        'test all territory links from Arena.wbt are in TERRITORY_LINKS'
        arena_links = set()
        with (REPO_ROOT / 'worlds' / 'Arena.wbt').open('r') as f:
            for line in f.readlines():
                if 'SRLink' in line:
                    arena_links.add(re.sub(r'.*DEF (.*) SRLink .*\n', r'\1', line))

        territory_links_strs = {'-'.join(link) for link in TERRITORY_LINKS}

        self.assertEqual(
            arena_links,
            territory_links_strs,
            'TERRITORY_LINKS differs from links in Arena.wbt',
        )

    def test_all_territories_linked(self) -> None:
        'test every territory exists in keys'
        station_codes = {station.value for station in StationCode}
        station_codes.update({zone.value for zone in TerritoryRoot})
        adjacent_stations = set(self.attached_territories.adjacent_zones.keys())

        self.assertEqual(
            station_codes,
            adjacent_stations,
            'Not all territories are linked',
        )

    def test_omitted_start_zones(self) -> None:
        'test PN, YL for incorrect links back to z0/z1'

        for station, links in self.attached_territories.adjacent_zones.items():
            self.assertNotIn(
                TerritoryRoot.z0,
                links,
                f'Zone 0 starting zone incorrectly appears in {station.value} links',
            )

            self.assertNotIn(
                TerritoryRoot.z1,
                links,
                f'Zone 1 starting zone incorrectly appears in {station.value} links',
            )

    def test_BE_links(self) -> None:
        'test BE for correct links'
        self.assertEqual(
            self.attached_territories.adjacent_zones[StationCode.BE],
            {StationCode.EY, StationCode.VB, StationCode.SZ, StationCode.PO},
            'Territory BE has incorrect territory links',
        )


class TestLiveScoring(unittest.TestCase):
    "Test the live scoring computed in the claim log using tests from the scorer"
    _tla_to_zone = {
        'ABC': Claimant.ZONE_0,
        'DEF': Claimant.ZONE_1,
    }

    def calculate_scores(
        self,
        territory_claims: List[Dict[str, Union[str, int, float]]],
    ) -> Mapping[Claimant, int]:
        claim_log = ClaimLog(record_arena_actions=False)

        for claim in territory_claims:
            territory = StationCode(claim['station_code'])
            claimant = Claimant(claim['zone'])
            claim_log._station_statuses[territory].owner = claimant

        return claim_log.get_scores()

    def assertScores(
        self,
        expected_scores_tla: Mapping[str, int],
        territory_claims: List[Dict[str, Union[str, int, float]]],
    ) -> None:
        actual_scores = self.calculate_scores(territory_claims)

        # swap the TLAs used by the scorer with claimant zones
        expected_scores: Mapping[Claimant, int] = {
            self._tla_to_zone[tla]: score
            for tla, score in expected_scores_tla.items()
        }

        self.assertEqual(expected_scores, actual_scores, "Wrong scores")

    # All tests below this line are copied from the scorer
    def test_no_claims(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 0,
        }, [])

    def test_single_claim(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4.432,
            },
        ])

    def test_two_claims_same_territory(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
        ])

    def test_two_concurrent_territories(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 5,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5.01,
            },
        ])

    def test_two_isolated_territories(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 5.01,
            },
        ])

    def test_both_teams_claim_both_territories(self) -> None:
        # But only one of them holds both at the same time
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 1,
                'station_code': 'EY',
                'time': 6,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 7,
            },
        ])

    def test_territory_becoming_unclaimed_after_it_was_claimed(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 6,
            },
            {
                'zone': -1,
                'station_code': 'PN',
                'time': 7,
            },
        ])

    def test_unclaimed_territory_with_others_claimed(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 6,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 7,
            },
            {
                'zone': -1,
                'station_code': 'PN',
                'time': 8,
            },
            {
                'zone': 1,
                'station_code': 'SZ',
                'time': 9,
            },
        ])


class TestTerritoryLockout(unittest.TestCase):
    "Test that individual territories become 'locked' when claimed a set number of times"

    _zone_0_territories = {StationCode.PN, StationCode.EY}
    _zone_1_territories = {StationCode.YL, StationCode.PO}

    def assertLocked(self, station: StationCode, context: str) -> None:
        self.assertTrue(
            self.territory_controller._claim_log.is_locked(station),
            f"Territory {station.value} not locked {context}",
        )

    def assertNotLocked(self, station: StationCode, context: str) -> None:
        self.assertFalse(
            self.territory_controller._claim_log.is_locked(station),
            f"Territory {station.value} locked {context}",
        )

    def claim_territory(self, station_code: StationCode, claimed_by: Claimant) -> None:
        self.territory_controller.claim_territory(station_code, claimed_by, claim_time=0)

    @patch('controller.Supervisor.getFromDef')
    @patch('territory_controller.get_robot_device')
    @patch('territory_controller.TerritoryController.set_score_display')
    @patch('territory_controller.TERRITORY_LINKS', new={
        (StationCode.PN, StationCode.EY),
        (TerritoryRoot.z0, StationCode.PN),
        (TerritoryRoot.z1, StationCode.PN),
    })
    def setUp(self, _: object, __: object, ___: object) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.attached_territories = AttachedTerritories(claim_log)
        self.territory_controller = TerritoryController(
            claim_log,
            self.attached_territories,
        )

    @patch('controller.Supervisor.getFromDef')
    @patch('territory_controller.LOCKED_OUT_AFTER_CLAIM', new=3)
    def test_territory_lockout(self, _: object) -> None:
        """
        Test a territory is locked after the correct number of claims and
        disconnected territories aren't also locked.

        The reduce map in this test looks like this:

            z0 ── PN ── z1
                   └─ EY

        Thus EY is claimable only after PN has been claimed and can easily
        become unclaimed when PN is claimed. This test is validating both that
        PN becomes locked at the right point and also that EY does not become
        locked at that point.
        """

        self.claim_territory(StationCode.PN, Claimant.ZONE_0)
        self.claim_territory(StationCode.EY, Claimant.ZONE_0)

        self.assertNotLocked(StationCode.PN, "early after first claims")
        self.assertNotLocked(StationCode.EY, "early after first claims")

        self.claim_territory(StationCode.PN, Claimant.ZONE_1)
        self.claim_territory(StationCode.EY, Claimant.ZONE_1)

        self.assertNotLocked(StationCode.PN, "early after second claims")
        self.assertNotLocked(StationCode.EY, "early after second claims")

        self.claim_territory(StationCode.PN, Claimant.ZONE_0)

        self.assertLocked(StationCode.PN, "after third claim")
        self.assertNotLocked(StationCode.EY, "after lock-out of PN")

    @patch('controller.Supervisor.getFromDef')
    def test_self_lockout(self, _: object) -> None:
        "Test a territory is locked after the correct number of claims by its own owner"
        for i in range(LOCKED_OUT_AFTER_CLAIM):
            # lock status is tested before capturing since the final
            # iteration will lock the territory
            self.assertNotLocked(StationCode.PN, f"early after {i+1} claims")

            self.claim_territory(StationCode.PN, Claimant.ZONE_0)

        self.assertLocked(StationCode.PN, f"after {LOCKED_OUT_AFTER_CLAIM} claims")
