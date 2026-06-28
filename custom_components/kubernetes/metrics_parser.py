"""Pure parsers for Kubernetes CPU and memory quantity strings.

Extracted from kubernetes_client.py so the conversion logic can be unit-tested
in isolation. These functions never raise: malformed, empty, or missing input
returns 0.0. (CPU "cores" output is rounded to a whole number; everything else
is rounded to 2 decimal places, preserving the original behavior.)
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# CPU: input suffix -> nanocores; output type -> divisor from nanocores.
_CPU_INPUT_MULTIPLIERS = {"n": 1, "u": 1000, "m": 1_000_000}
_CPU_OUTPUT_DIVISORS = {"n": 1, "u": 1000, "m": 1_000_000, "cores": 1_000_000_000}

# Memory: binary (Ki..) and decimal (k..) suffixes -> bytes; output -> divisor.
_MEMORY_BINARY_PREFIXES = {
    "Ki": 1024,
    "Mi": 1024**2,
    "Gi": 1024**3,
    "Ti": 1024**4,
    "Pi": 1024**5,
    "Ei": 1024**6,
}
_MEMORY_DECIMAL_PREFIXES = {
    "k": 1000,
    "M": 1000**2,
    "G": 1000**3,
    "T": 1000**4,
    "P": 1000**5,
    "E": 1000**6,
}
_MEMORY_OUTPUT_MULTIPLIERS = {"KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}


def parse_cpu_quantity(cpu_str: str, output_type: str = "cores") -> float:
    """Parse a Kubernetes CPU quantity to the given unit (n, u, m, or cores)."""
    try:
        nanocores = 0.0
        for suffix, multiplier in _CPU_INPUT_MULTIPLIERS.items():
            if cpu_str.endswith(suffix):
                nanocores = float(cpu_str[: -len(suffix)]) * multiplier
                break
        else:
            nanocores = float(cpu_str) * 1_000_000_000

        divisor = _CPU_OUTPUT_DIVISORS.get(output_type, 1_000_000_000)
        if output_type not in _CPU_OUTPUT_DIVISORS:
            _LOGGER.warning(
                "Invalid output type '%s', defaulting to cores", output_type
            )
        value = nanocores / divisor
        if output_type == "cores" or output_type not in _CPU_OUTPUT_DIVISORS:
            return int(round(value))
        return round(value, 2)
    except (ValueError, IndexError, TypeError, AttributeError):
        _LOGGER.warning("Failed to parse CPU string: %s", cpu_str)
        return 0.0


def parse_memory_quantity(memory_str: str, output_type: str = "MiB") -> float:
    """Parse a Kubernetes memory quantity to the given unit (KiB, MiB, or GiB)."""
    try:
        bytes_value = 0.0
        for suffix, multiplier in _MEMORY_BINARY_PREFIXES.items():
            if memory_str.endswith(suffix):
                bytes_value = float(memory_str[: -len(suffix)]) * multiplier
                break
        else:
            for suffix, multiplier in _MEMORY_DECIMAL_PREFIXES.items():
                if memory_str.endswith(suffix):
                    bytes_value = float(memory_str[: -len(suffix)]) * multiplier
                    break
            else:
                bytes_value = float(memory_str)

        multiplier = _MEMORY_OUTPUT_MULTIPLIERS.get(output_type, 1024**2)
        if output_type not in _MEMORY_OUTPUT_MULTIPLIERS:
            _LOGGER.warning("Invalid output type '%s', defaulting to MiB", output_type)
        return round(bytes_value / multiplier, 2)
    except (ValueError, IndexError, TypeError, AttributeError):
        _LOGGER.warning("Failed to parse memory string: %s", memory_str)
        return 0.0
