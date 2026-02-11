from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass(frozen=True)
class Equation:
    name: str
    expression: str
    variables: Dict[str, str]


class EquationLibrary:
    def __init__(self):
        self._equations: List[Equation] = []
        self._index: Dict[str, Set[int]] = {}
        self._load_equations()
        self._build_index()

    def _load_equations(self):
        self._equations = [
            Equation(
                name="Ohm's Law",
                expression="V = I R",
                variables={"V": "Potential difference", "I": "Current", "R": "Resistance"}
            ),
            Equation(
                name="Hooke's Law",
                expression="F = k x",
                variables={"F": "Force", "k": "Spring constant", "x": "Extension"}
            ),
            Equation(
                name="Kinetic Energy",
                expression="E = 1/2 m v^2",
                variables={"E": "Energy", "m": "Mass", "v": "Velocity"}
            ),
            Equation(
                name="Ideal Gas Law",
                expression="P V = n R T",
                variables={"P": "Pressure", "V": "Volume", "n": "Amount of substance", "R": "Gas constant", "T": "Temperature"}
            ),
            Equation(
                name="Density",
                expression="ρ = m / V",
                variables={"ρ": "Density", "m": "Mass", "V": "Volume"}
            ),
            Equation(
                name="Wave Speed",
                expression="v = f λ",
                variables={"v": "Wave speed", "f": "Frequency", "λ": "Wavelength"}
            ),
            Equation(
                name= "Magnetic Field",
                expression= "F = B Q v",
                variables= {"F": "Force","B": "Magnetic flux density", "Q": "Charge", "v": "Velocity"}
            ),
        ]

    def _build_index(self):
        for idx, eq in enumerate(self._equations):
            tokens = set()
            tokens.update(eq.name.lower().split())
            tokens.update(eq.expression.replace("=", " ").split())
            for symbol, meaning in eq.variables.items():
                tokens.add(symbol.lower())
                tokens.update(meaning.lower().split())
            for token in tokens:
                self._index.setdefault(token, set()).add(idx)

    def search(self, query: str) -> List[Equation]:
        if not query:
            return []
        query_tokens = query.lower().split()
        matched: Set[int] = set()
        for token in query_tokens:
            if token in self._index:
                matched = self._index[token] if not matched else matched & self._index[token]
        return [self._equations[i] for i in matched]