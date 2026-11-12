"""Purge VMs, floating IPs, and reservations across enabled cloud providers."""

from __future__ import annotations

import click

from cloudmesh.ai.command._shared.context import (
    console,
    get_enabled_providers,
    vm_options,
)
from cloudmesh.ai.command._shared.exceptions import handle_errors


@click.command(name="purge")
@click.confirmation_option(
    "--yes",
    "-y",
    prompt="Are you sure you want to delete all VMs, floating IPs, and reservations?",
)
@vm_options
@click.pass_context
@handle_errors
def purge_cmd(
    ctx: click.Context,
    cloud: str | None = None,
    verbose: bool = False,
    debug: bool = False,
    **kwargs,
) -> None:
    """Delete all VMs, release floating IPs, and remove reservations."""
    providers = get_enabled_providers(ctx, cloud=cloud)
    if not providers:
        console.print("[yellow]No enabled providers found; nothing to delete.[/yellow]")
        return

    deleted_vms = 0
    released_fips = 0
    deleted_res = 0
    failures = 0

    for cloud_name, provider in providers:
        console.print(f"[bold cyan]=== Purging: {cloud_name} ===[/bold cyan]")

        vms = []
        try:
            vms = provider.list() if hasattr(provider, "list") else []
        except Exception as exc:
            console.print(f"[red]Error listing VMs on {cloud_name}: {exc}[/red]")
            failures += 1

        if not vms:
            console.print(f"[dim]{cloud_name}: nothing to delete for VMs.[/dim]")
        for vm in vms or []:
            vm_name = (
                vm.get("name") if isinstance(vm, dict) else getattr(vm, "name", str(vm))
            )
            try:
                provider.delete(vm_name)
                console.print(f"[green]Deleted VM:[/green] {vm_name}")
                deleted_vms += 1
            except Exception as exc:
                console.print(f"[red]Failed to delete VM {vm_name}: {exc}[/red]")
                failures += 1

        fips = []
        if hasattr(provider, "list_floating_ips"):
            try:
                fips = provider.list_floating_ips() or []
            except Exception as exc:
                console.print(
                    f"[red]Error listing floating IPs on {cloud_name}: {exc}[/red]"
                )
                failures += 1

        if not fips:
            console.print(
                f"[dim]{cloud_name}: nothing to delete for floating IPs.[/dim]"
            )
        for fip in fips:
            addr = (
                fip.get("ip") or fip.get("floating_ip_address")
                if isinstance(fip, dict)
                else str(fip)
            )
            try:
                if hasattr(provider, "release_floating_ip_by_ip"):
                    provider.release_floating_ip_by_ip(addr)
                elif hasattr(provider, "release_floating_ip"):
                    provider.release_floating_ip(addr)
                console.print(f"[green]Released floating IP:[/green] {addr}")
                released_fips += 1
            except Exception as exc:
                console.print(f"[red]Failed to release floating IP {addr}: {exc}[/red]")
                failures += 1

        reservations = []
        if hasattr(provider, "list_reservations"):
            try:
                reservations = provider.list_reservations() or []
            except Exception as exc:
                console.print(
                    f"[red]Error listing reservations on {cloud_name}: {exc}[/red]"
                )
                failures += 1

        if not reservations:
            console.print(
                f"[dim]{cloud_name}: nothing to delete for reservations.[/dim]"
            )
        for res in reservations:
            res_id = res.get("id") if isinstance(res, dict) else str(res)
            try:
                if hasattr(provider, "delete_reservation"):
                    provider.delete_reservation(res_id)
                console.print(f"[green]Deleted reservation:[/green] {res_id}")
                deleted_res += 1
            except Exception as exc:
                console.print(
                    f"[red]Failed to delete reservation {res_id}: {exc}[/red]"
                )
                failures += 1

    console.print(
        f"[bold]Purge summary:[/bold] {deleted_vms} VMs deleted, "
        f"{released_fips} floating IPs released, "
        f"{deleted_res} reservations deleted, {failures} failures."
    )


cmd = purge_cmd
