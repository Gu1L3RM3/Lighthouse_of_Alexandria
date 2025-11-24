from core.settings import PREFIXES
class SetterValues:
        
        
    @staticmethod
    def format_eng(value: float, unit: str) -> str:
        """

        Args:
            value: O número a ser formatado.
            unit: A unidade base (ex: 'V', 'A', 'Hz').

        Returns:
            Uma string formatada (ex: "1.23 kV", "500.00 µA").
        """
        if value == 0:
            return f"0.00{unit}"

        

        for multiplier, prefix in PREFIXES:
            if abs(value) >= multiplier:
                scaled_value = value / multiplier
                return f"{scaled_value:.2f}{prefix}{unit}"
        
        return f"{value:.2e}{unit}"