"""Pure parsers for Kubernetes CPU and memory quantity strings.

Extracted from kubernetes_client.py so the conversion logic can be unit-tested
in isolation. These functions never raise: malformed, empty, or missing input
returns 0.0. Every Kubernetes quantity suffix is accepted for both resources
(n/u/m, k/M/G/T/P/E and Ki..Ei). (CPU "cores" output is rounded to a whole
number; everything else is rounded to 2 decimal places, preserving the
original behavior.)
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# Kubernetes quantity suffixes (resource.Quantity grammar, case-sensitive) ->
# exact (numerator, denominator) scale of the base unit (cores or bytes). The
# same grammar applies to every resource, so CPU may carry "k"/"Ki" and memory
# "m". Two-char binary suffixes are listed first so they match before any
# single-char one. Exponent forms ("1e3", "1E3") end in a digit, match no
# suffix and go straight to float(); a bare "E" suffix is exa. A value with an
# unrecognized suffix makes float() raise, which callers catch (returning 0.0).
_QUANTITY_SUFFIXES: dict[str, tuple[int, int]] = {
    "Ki": (1024, 1),
    "Mi": (1024**2, 1),
    "Gi": (1024**3, 1),
    "Ti": (1024**4, 1),
    "Pi": (1024**5, 1),
    "Ei": (1024**6, 1),
    "n": (1, 1000**3),
    "u": (1, 1000**2),
    "m": (1, 1000),
    "k": (1000, 1),
    "M": (1000**2, 1),
    "G": (1000**3, 1),
    "T": (1000**4, 1),
    "P": (1000**5, 1),
    "E": (1000**6, 1),
}

# CPU output type -> divisor from nanocores.
_NANOCORES_PER_CORE = 1_000_000_000
_CPU_OUTPUT_DIVISORS = {"n": 1, "u": 1000, "m": 1_000_000, "cores": 1_000_000_000}

# Memory output type -> divisor from bytes.
_MEMORY_OUTPUT_MULTIPLIERS = {"KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}


def _quantity_to_base(quantity: str, base_scale: int = 1) -> float:
    """Convert a quantity string to ``base_scale`` sub-units of its base unit.

    ``base_scale`` (e.g. 10**9 for nanocores) is folded into the integer scale
    before dividing, so whole-number results such as "500m" -> 500_000_000
    nanocores stay exact. Raises ValueError/AttributeError on bad input.
    """
    for suffix, (numerator, denominator) in _QUANTITY_SUFFIXES.items():
        if quantity.endswith(suffix):
            number = float(quantity[: -len(suffix)])
            return number * numerator * base_scale / denominator
    return float(quantity) * base_scale


def parse_cpu_quantity(cpu_str: str, output_type: str = "cores") -> float:
    """Parse a Kubernetes CPU quantity to the given unit (n, u, m, or cores)."""
    try:
        nanocores = _quantity_to_base(cpu_str, _NANOCORES_PER_CORE)

        divisor = _CPU_OUTPUT_DIVISORS.get(output_type, 1_000_000_000)
        if output_type not in _CPU_OUTPUT_DIVISORS:
            _LOGGER.warning(
                "Invalid output type '%s', defaulting to cores", output_type
            )
        value = nanocores / divisor
        if output_type == "cores" or output_type not in _CPU_OUTPUT_DIVISORS:
            return round(value)
        return round(value, 2)
    except (ValueError, IndexError, TypeError, AttributeError):
        _LOGGER.warning("Failed to parse CPU string: %s", cpu_str)
        return 0.0


def parse_memory_quantity(memory_str: str, output_type: str = "MiB") -> float:
    """Parse a Kubernetes memory quantity to the given unit (KiB, MiB, or GiB)."""
    try:
        bytes_value = _quantity_to_base(memory_str)

        multiplier = _MEMORY_OUTPUT_MULTIPLIERS.get(output_type, 1024**2)
        if output_type not in _MEMORY_OUTPUT_MULTIPLIERS:
            _LOGGER.warning("Invalid output type '%s', defaulting to MiB", output_type)
        return round(bytes_value / multiplier, 2)
    except (ValueError, IndexError, TypeError, AttributeError):
        _LOGGER.warning("Failed to parse memory string: %s", memory_str)
        return 0.0
