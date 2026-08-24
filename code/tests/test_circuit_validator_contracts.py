import unittest

from core.systems.circuit_validators.circuit_validator_system import CircuitValidatorSystem
from core.systems.circuit_validators.max_power_transfer_validator_system import MaxPowerTransferValidatorSystem
from core.systems.circuit_validators.resistor_association_validator_system import ResistorAssociationValidatorSystem
from core.systems.circuit_validators.resistor_pair_validator_system import ResistorPairValidatorSystem
from core.systems.circuit_validators.thevenin_norton_validator_system import TheveninNortonValidatorSystem


class CircuitValidatorContractTests(unittest.TestCase):
    def test_all_validators_accept_the_circuit_service_contract(self):
        service = object()
        validators = (
            CircuitValidatorSystem("phase", circuit_service=service),
            ResistorPairValidatorSystem("phase", circuit_service=service),
            ResistorAssociationValidatorSystem("phase", circuit_service=service),
            TheveninNortonValidatorSystem("phase", circuit_service=service),
            MaxPowerTransferValidatorSystem("phase", circuit_service=service),
        )

        for validator in validators:
            self.assertIs(validator.circuits, service)


if __name__ == "__main__":
    unittest.main()
