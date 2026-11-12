"""Unit tests for cmx vm status command (Issue #116)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cloudmesh.ai.command.vm.status import status_cmd


def test_vm_status_displays_vms_fips_and_reservations():
    runner = CliRunner()
    mock_provider = MagicMock()
    mock_provider.list.return_value = [
        {"name": "vm-1", "status": "Running", "ip": "10.0.0.5"}
    ]
    mock_provider.list_floating_ips.return_value = [
        {"ip": "129.114.10.20", "status": "ACTIVE"}
    ]
    mock_provider.list_reservations.return_value = [
        {"id": "lease-1", "name": "test-lease", "status": "ACTIVE"}
    ]

    with patch(
        "cloudmesh.ai.command.vm.status.get_enabled_providers",
        return_value=[("chameleon", mock_provider)],
    ):
        result = runner.invoke(status_cmd, ["--cloud", "chameleon"])

    assert result.exit_code == 0
    assert "chameleon" in result.output
    mock_provider.list.assert_called_once()
    mock_provider.list_floating_ips.assert_called_once()
    mock_provider.list_reservations.assert_called_once()


def test_vm_status_handles_empty_resources():
    runner = CliRunner()
    mock_provider = MagicMock()
    mock_provider.list.return_value = []
    mock_provider.list_floating_ips.return_value = []
    mock_provider.list_reservations.return_value = []

    with patch(
        "cloudmesh.ai.command.vm.status.get_enabled_providers",
        return_value=[("multipass", mock_provider)],
    ):
        result = runner.invoke(status_cmd, ["--cloud", "multipass"])

    assert result.exit_code == 0
    assert "none" in result.output.lower()
