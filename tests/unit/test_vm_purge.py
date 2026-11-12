"""Unit tests for cmx vm purge command (Issue #116)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cloudmesh.ai.command.vm.purge import purge_cmd


def test_vm_purge_deletes_vms_fips_and_reservations_with_yes():
    runner = CliRunner()
    mock_provider = MagicMock()
    mock_provider.list.return_value = [{"name": "node-1"}, {"name": "node-2"}]
    mock_provider.list_floating_ips.return_value = [{"ip": "149.165.10.1"}]
    mock_provider.list_reservations.return_value = [{"id": "res-99"}]

    with patch(
        "cloudmesh.ai.command.vm.purge.get_enabled_providers",
        return_value=[("chameleon", mock_provider)],
    ):
        result = runner.invoke(purge_cmd, ["--cloud", "chameleon", "--yes"])

    assert result.exit_code == 0
    assert mock_provider.delete.call_count == 2
    mock_provider.release_floating_ip_by_ip.assert_called_once_with("149.165.10.1")
    mock_provider.delete_reservation.assert_called_once_with("res-99")
    assert "2 VMs deleted" in result.output


def test_vm_purge_idempotent_when_empty():
    runner = CliRunner()
    mock_provider = MagicMock()
    mock_provider.list.return_value = []
    mock_provider.list_floating_ips.return_value = []
    mock_provider.list_reservations.return_value = []

    with patch(
        "cloudmesh.ai.command.vm.purge.get_enabled_providers",
        return_value=[("multipass", mock_provider)],
    ):
        result = runner.invoke(purge_cmd, ["--cloud", "multipass", "-y"])

    assert result.exit_code == 0
    assert "nothing to delete" in result.output.lower()
    assert "0 VMs deleted" in result.output


def test_vm_purge_continues_on_error_and_prompts_without_yes():
    runner = CliRunner()
    mock_provider = MagicMock()
    mock_provider.list.return_value = [{"name": "bad-vm"}, {"name": "good-vm"}]
    mock_provider.delete.side_effect = [RuntimeError("delete failed"), True]
    mock_provider.list_floating_ips.return_value = []
    mock_provider.list_reservations.return_value = []

    with patch(
        "cloudmesh.ai.command.vm.purge.get_enabled_providers",
        return_value=[("multipass", mock_provider)],
    ):
        abort_res = runner.invoke(purge_cmd, ["--cloud", "multipass"], input="n\n")
        assert abort_res.exit_code != 0

        ok_res = runner.invoke(purge_cmd, ["--cloud", "multipass", "--yes"])
        assert ok_res.exit_code == 0
        assert "1 VMs deleted" in ok_res.output
        assert "1 failures" in " ".join(ok_res.output.split())
