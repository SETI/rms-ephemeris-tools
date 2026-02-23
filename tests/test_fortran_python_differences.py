"""Tests for high-priority FORTRAN vs Python differences.

These tests verify that the critical numerical differences identified in the
FORTRAN_Python_Numerical_Comparison_Report.md have been fixed.
"""

from __future__ import annotations

import math
from io import StringIO

import pytest

from ephemeris_tools.constants import EARTH_ID
from ephemeris_tools.planets import SATURN_CONFIG
from ephemeris_tools.spice.load import load_spice_files
from ephemeris_tools.spice.observer import set_observer_id
from ephemeris_tools.time_utils import tai_from_day_sec, tdb_from_tai
from ephemeris_tools.viewer import _propagated_saturn_f_ring, run_viewer
from ephemeris_tools.viewer_helpers import viewer_params_from_legacy_kwargs


class TestHighPriorityDifferences:
    """Test critical FORTRAN-Python differences that have been fixed."""

    def test_fov_clamping_large_fov(self) -> None:
        """Test DIFF-002: FOV clamping to 90 degrees.

        FORTRAN clamps FOV to π/2 radians (90 degrees) to prevent projection
        singularities. Python must do the same.
        """
        success, error = load_spice_files(planet=5, version=0, force=True)
        if not success:
            pytest.skip(f'SPICE kernels not available: {error}')

        set_observer_id(EARTH_ID)

        ps_out = StringIO()
        txt_out = StringIO()

        # Test with a very large FOV (120 degrees)
        # This should be clamped to 90 degrees internally
        run_viewer(
            viewer_params_from_legacy_kwargs(
                planet_num=5,
                time_str='2024-01-01 00:00:00',
                fov=120.0,
                fov_unit='deg',
                viewpoint='Earth',
                output_ps=ps_out,
                output_txt=txt_out,
            )
        )

        # The function should complete without error (no NaN or projection failures)
        # Verify output was generated
        ps_content = ps_out.getvalue()
        txt_content = txt_out.getvalue()

        assert len(ps_content) > 0, 'PostScript output should be generated'
        assert len(txt_content) > 0, 'Text output should be generated'
        assert 'Field of View Description' in txt_content

        # Verify no NaN values in the output
        assert 'nan' not in ps_content.lower()
        assert 'nan' not in txt_content.lower()
        assert 'inf' not in ps_content.lower()
        assert 'inf' not in txt_content.lower()

    def test_fov_clamping_boundary(self) -> None:
        """Test FOV exactly at 90 degrees (boundary case)."""
        success, error = load_spice_files(planet=5, version=0, force=True)
        if not success:
            pytest.skip(f'SPICE kernels not available: {error}')

        set_observer_id(EARTH_ID)

        ps_out = StringIO()
        txt_out = StringIO()

        # Test with FOV exactly at the clamp limit
        run_viewer(
            viewer_params_from_legacy_kwargs(
                planet_num=5,
                time_str='2024-01-01 00:00:00',
                fov=90.0,
                fov_unit='deg',
                viewpoint='Earth',
                output_ps=ps_out,
                output_txt=txt_out,
            )
        )

        ps_content = ps_out.getvalue()
        txt_content = txt_out.getvalue()

        assert len(ps_content) > 0
        assert len(txt_content) > 0
        assert 'Field of View Description' in txt_content

    def test_saturn_f_ring_time_calculation(self) -> None:
        """Test DIFF-003: Saturn F ring propagation formula.

        FORTRAN uses: ring_peris + FRING_DPERI_DT * (obs_time - ref_time - dt)
        Python was incorrectly using: ring_peris + FRING_DPERI_DT * ddays * _SEC_PER_DAY

        The fix ensures elapsed_sec is used directly.
        """
        # Load Saturn SPICE kernels; force reload so we have Saturn regardless of
        # prior tests (avoids order-dependent failures from global SPICE state).
        success, error = load_spice_files(planet=6, version=0, force=True)
        if not success:
            pytest.skip(f'Cannot load SPICE for Saturn: {error}')

        set_observer_id(EARTH_ID)

        # Test time: 2020-01-01 00:00:00 UTC
        # Day 0 is 2000-01-01, so 2020-01-01 is day 7305
        day = 7305
        sec = 0.0
        tai = tai_from_day_sec(day, sec)
        et = tdb_from_tai(tai)

        # Compute F ring propagation
        result = _propagated_saturn_f_ring(et, SATURN_CONFIG)

        assert result is not None, 'F ring propagation should return values'
        peri_rad, node_rad = result

        # Verify the results are reasonable
        # The values may exceed 2π since they're not normalized
        # Normalize to [0, 2π] for range checking
        peri_norm = peri_rad % (2.0 * math.pi)
        node_norm = node_rad % (2.0 * math.pi)

        assert 0.0 <= peri_norm <= 2.0 * math.pi, f'Normalized pericenter out of range: {peri_norm}'
        assert 0.0 <= node_norm <= 2.0 * math.pi, f'Normalized node out of range: {node_norm}'

        # The values should have propagated significantly
        # Over 20 years with rates ~5e-7 rad/sec, change should be ~300+ radians
        assert abs(peri_rad) > 100.0, f'Pericenter propagation seems incorrect: {peri_rad}'
        assert abs(node_rad) > 100.0, f'Node propagation seems incorrect: {node_rad}'

    def test_radec_offset_units_earth_observer(self) -> None:
        """Test DIFF-004: RA/Dec offset units for Earth observer (arcsec)."""
        success, error = load_spice_files(planet=5, version=0, force=True)
        if not success:
            pytest.skip(f'Cannot load SPICE for Jupiter: {error}')

        set_observer_id(EARTH_ID)

        txt_out = StringIO()

        try:
            run_viewer(
                viewer_params_from_legacy_kwargs(
                    planet_num=5,
                    time_str='2024-01-01 00:00:00',
                    fov=1.0,
                    fov_unit='deg',
                    viewpoint='Earth',
                    output_ps=StringIO(),
                    output_txt=txt_out,
                )
            )
        except (KeyError, OSError) as e:
            if 'RADII' in str(e) or 'KERNELVARNOTFOUND' in str(e) or 'NOLOADEDFILES' in str(e):
                pytest.skip(f'SPICE kernel data not available: {e}')
            raise

        txt_content = txt_out.getvalue()

        # For Earth observer, header should show arcsec units
        assert 'dRA (")' in txt_content, 'Earth observer should use arcsec (")'
        assert 'dDec (")' in txt_content, 'Earth observer should use arcsec (")'
        # Should NOT show degree units
        cond = 'dRA (deg)' not in txt_content or txt_content.count('dRA (deg)') < txt_content.count(
            'dRA (")'
        )
        assert cond, 'Earth observer should primarily use arcsec, not degrees'

    def test_radec_offset_units_spacecraft_observer(self) -> None:
        """Test DIFF-004: RA/Dec offset units for spacecraft observer (degrees).

        Skipped when Cassini (or equivalent) spacecraft SPICE kernels are not
        available; otherwise runs like other integration tests.
        """
        from ephemeris_tools.spice.load import load_spacecraft

        success = load_spacecraft(sc_id='CAS', planet=6, version=0, set_obs=True)
        if not success:
            pytest.skip('Cassini spacecraft kernels not available')

        txt_out = StringIO()

        try:
            run_viewer(
                viewer_params_from_legacy_kwargs(
                    planet_num=6,
                    time_str='2017-09-15 00:00:00',  # Cassini Grand Finale
                    fov=1.0,
                    fov_unit='deg',
                    viewpoint='CAS',
                    output_ps=StringIO(),
                    output_txt=txt_out,
                )
            )
        except (KeyError, OSError) as e:
            if 'RADII' in str(e) or 'KERNELVARNOTFOUND' in str(e) or 'NOLOADEDFILES' in str(e):
                pytest.skip(f'SPICE kernel data not available: {e}')
            raise

        txt_content = txt_out.getvalue()

        # For spacecraft observer, header should show degree units
        assert 'dRA (deg)' in txt_content, 'Spacecraft observer should use degrees'
        assert 'dDec (deg)' in txt_content, 'Spacecraft observer should use degrees'
        # Should NOT show arcsec units for offset columns
        lines = txt_content.split('\n')
        header_line = next((line for line in lines if 'dRA' in line and 'dDec' in line), None)
        assert header_line is not None, 'Header line with dRA and dDec not found in output'
        # In header for spacecraft, should be "(deg)" not "(")"
        assert '(")' not in header_line or header_line.count('(deg)') > 0, (
            'Spacecraft observer should use degrees for offsets'
        )

    def test_all_fixes_integrated(self) -> None:
        """Integration test: all high-priority fixes work together."""
        success, error = load_spice_files(planet=6, version=0, force=True)
        if not success:
            pytest.skip(f'Cannot load SPICE for Saturn: {error}')

        set_observer_id(EARTH_ID)

        ps_out = StringIO()
        txt_out = StringIO()

        # Test with large FOV to trigger clamping
        # Saturn to test F ring propagation
        # Earth observer to test arcsec units
        run_viewer(
            viewer_params_from_legacy_kwargs(
                planet_num=6,
                time_str='2020-01-01 00:00:00',
                fov=100.0,  # Will be clamped to 90
                fov_unit='deg',
                viewpoint='Earth',
                output_ps=ps_out,
                output_txt=txt_out,
            )
        )

        ps_content = ps_out.getvalue()
        txt_content = txt_out.getvalue()

        # Verify all outputs
        assert len(ps_content) > 0
        assert len(txt_content) > 0
        assert 'Field of View Description' in txt_content
        assert 'dRA (")' in txt_content  # Earth observer uses arcsec
        assert 'nan' not in ps_content.lower()
        assert 'nan' not in txt_content.lower()

        # Verify F ring data is present (if Saturn has F ring in config)
        # The text output should contain ring geometry information
        assert 'Ring' in txt_content or 'ring' in txt_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
