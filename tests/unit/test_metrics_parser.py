"""Unit tests for the pure CPU/memory quantity parsers."""

import pytest

from custom_components.kubernetes.metrics_parser import (
    parse_cpu_quantity,
    parse_memory_quantity,
)


class TestParseCpuQuantity:
    @pytest.mark.parametrize(
        ("value", "output_type", "expected"),
        [
            ("500m", "m", 500.0),
            ("250m", "m", 250.0),
            ("1500000u", "m", 1500.0),
            ("2", "cores", 2),
            ("1500m", "cores", 2),  # 1.5 cores -> round(1.5) == 2 (banker's rounding)
            ("500m", "cores", 0),  # 0.5 cores -> round(0.5) == 0
            ("1000000000n", "cores", 1),
            ("1000m", "n", 1000000000.0),  # 1 core in nanocores
            ("1000m", "u", 1000000.0),  # 1 core in microcores
            ("-100m", "m", -100.0),  # negatives pass through unclamped
            ("10k", "cores", 10000),  # virtual-kubelet node capacity
            ("1k", "m", 1000000.0),
            ("2Ki", "cores", 2048),
            ("1M", "cores", 1000000),
            ("1e3", "cores", 1000),  # exponent form, not a suffix
            ("1E", "cores", 10**18),  # bare "E" is the exa suffix
            ("0.5", "m", 500.0),
            (
                "100m",
                "invalid",
                0,
            ),  # unknown output type -> cores semantics, int rounding
        ],
    )
    def test_valid(self, value, output_type, expected):
        assert parse_cpu_quantity(value, output_type) == expected

    @pytest.mark.parametrize("bad", ["abc", "", None, "12x", "1K", object()])
    def test_bad_input_returns_zero(self, bad):
        assert parse_cpu_quantity(bad) == 0.0

    def test_default_output_type_is_cores(self):
        assert parse_cpu_quantity("2000m") == 2


class TestParseMemoryQuantity:
    @pytest.mark.parametrize(
        ("value", "output_type", "expected"),
        [
            ("2Ki", "KiB", 2.0),
            ("3Gi", "MiB", 3072.0),
            ("1Mi", "MiB", 1.0),
            ("1Gi", "GiB", 1.0),
            ("512Mi", "GiB", 0.5),
            ("100M", "MiB", 95.37),  # 100*10^6 bytes / 1024^2
            ("1048576", "MiB", 1.0),  # plain bytes
            ("1073741824000m", "GiB", 1.0),  # milli-bytes
            ("1073741824000000u", "GiB", 1.0),
            ("1073741824000000000n", "GiB", 1.0),
            ("1e3", "KiB", 0.98),  # exponent form, not a suffix
            ("1Ei", "GiB", 1024.0**3),
            ("1E", "GiB", 931322574.62),  # 10^18 / 1024^3
            ("1Gi", "invalid", 1024.0),  # unknown output type -> defaults to MiB
        ],
    )
    def test_valid(self, value, output_type, expected):
        assert parse_memory_quantity(value, output_type) == expected

    @pytest.mark.parametrize("bad", ["abc", "", None, "5Q", "1K", object()])
    def test_bad_input_returns_zero(self, bad):
        assert parse_memory_quantity(bad) == 0.0
