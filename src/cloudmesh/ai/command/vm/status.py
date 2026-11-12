"""Display VM, floating IP, and reservation status across enabled cloud providers."""

from __future__ import annotations

from typing import Any

import click

from cloudmesh.ai.command._shared.context import (
    console,
    get_enabled_providers,
    vm_options,
)
from cloudmesh.ai.command._shared.exceptions import handle_errors
from cloudmesh.ai.command._shared.ui import render_table


def _render_section(title: str, columns: list[str], rows: list[list[Any]]) -> None:
    """Render a status section table or report when empty."""
    if not rows:
        console.print(f"[dim]{title}: none[/dim]")
        return
    render_table(title, columns, rows)


@click.command(name="status")
@vm_options
@click.pass_context
@handle_errors
def status_cmd(
    ctx: click.Context,
    cloud: str | None = None,
    verbose: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> None:
    """Show active VMs, floating IPs, and reservations for enabled providers."""
    providers = get_enabled_providers(ctx, cloud=cloud)
    if not providers:
        console.print("[yellow]No enabled providers found.[/yellow]")
        return

    for cloud_name, provider in providers:
        console.print(f"[bold cyan]=== Status: {cloud_name} ===[/bold cyan]")
        try:
            vms_raw = provider.list() if hasattr(provider, "list") else []
        except Exception as exc:
            console.print(f"[red]Failed to list VMs on {cloud_name}: {exc}[/red]")
            vms_raw = []

        vm_rows: list[list[Any]] = []
        for vm in vms_raw or []:
            if isinstance(vm, dict):
                vm_rows.append(
                    [
                        vm.get("name", "Unknown"),
                        vm.get("status", "Unknown"),
                        vm.get("ip", "N/A"),
                    ]
                )
            else:
                vm_rows.append(
                    [
                        getattr(vm, "name", "Unknown"),
                        getattr(vm, "status", "Unknown"),
                        getattr(vm, "ip", "N/A"),
                    ]
                )
        _render_section(f"VMs ({cloud_name})", ["Name", "Status", "IP"], vm_rows)

        fip_rows: list[list[Any]] = []
        if hasattr(provider, "list_floating_ips"):
            try:
                for fip in provider.list_floating_ips() or []:
                    if isinstance(fip, dict):
                        fip_rows.append(
                            [
                                fip.get("ip")
                                or fip.get("floating_ip_address", "Unknown"),
                                fip.get("status", "Unknown"),
                            ]
                        )
                    else:
                        fip_rows.append([str(fip), "ACTIVE"])
            except Exception as exc:
                console.print(
                    f"[red]Failed to list floating IPs on {cloud_name}: {exc}[/red]"
                )
        _render_section(
            f"Floating IPs ({cloud_name})", ["IP Address", "Status"], fip_rows
        )

        res_rows: list[list[Any]] = []
        if hasattr(provider, "list_reservations"):
            try:
                for res in provider.list_reservations() or []:
                    if isinstance(res, dict):
                        res_rows.append(
                            [
                                res.get("id", "Unknown"),
                                res.get("name", "N/A"),
                                res.get("status", "Unknown"),
                            ]
                        )
                    else:
                        res_rows.append([str(res), "N/A", "ACTIVE"])
            except Exception as exc:
                console.print(
                    f"[red]Failed to list reservations on {cloud_name}: {exc}[/red]"
                )
        _render_section(
            f"Reservations ({cloud_name})", ["ID", "Name", "Status"], res_rows
        )


cmd = status_cmd
