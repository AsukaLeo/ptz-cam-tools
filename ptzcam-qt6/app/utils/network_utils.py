# -*- coding: utf-8 -*-

# Copyright (C) 2026 Asuka
#
# This file is part of PTZ-Cam-Tools.
#
# PTZ-Cam-Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PTZ-Cam-Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PTZ-Cam-Tools. If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-only

"""Network interface utility functions shared across video source tabs."""

import socket
from typing import Optional
from app.utils.logger import get_logger


def is_physical_nic(name: str) -> bool:
    """Check if a network interface name corresponds to a physical NIC.

    Filters out virtual adapters (VMware, Hyper-V, Docker, VPN, etc.)
    by matching against known virtual adapter keywords.

    Args:
        name: Network interface name.

    Returns:
        True if the interface appears to be a physical NIC.
    """
    name_lower = name.lower()
    virtual_keywords = [
        # English
        'vmware', 'vmnet', 'virtualbox', 'vbox',
        'hyper-v', 'v ethernet', 'default switch',
        'docker', 'veth', 'br-',
        'bluetooth', 'bluetooh',
        'loopback', 'isatap', '6to4',
        'tap-', 'tap-windows',
        'openvpn', 'tun-', 'tun0',
        'npcap', 'npcappacket',
        'pseudo', 'virtual',
        'microsoft wi-fi direct',
        'localhost', 'software',
        'wsl',
        # Chinese (for localized Windows)
        '蓝牙', '虚拟', '回环', '隧道', '本地连接',
    ]
    for kw in virtual_keywords:
        if kw in name_lower:
            return False
    return True


def get_nic_choices() -> list[str]:
    """Enumerate physical network interfaces and build display strings.

    Each display string includes the interface name and ONE IPv4 address.
    If an interface has multiple IPv4 addresses, multiple entries are
    created (one per IP) so QComboBox can display them as separate rows.

    Returns:
        List of formatted NIC display strings, e.g.
        ["以太网 - 192.168.1.100", "以太网 - 192.168.2.100", "Wi-Fi - 10.0.0.5"]
    """
    logger = get_logger(__name__)
    choices: list[str] = []

    try:
        import psutil
        addrs = psutil.net_if_addrs()
    except ImportError:
        logger.warning("psutil not available for NIC enumeration")
        return choices

    for iface_name, snic_list in addrs.items():
        if not is_physical_nic(iface_name):
            continue

        # Collect all IPv4 addresses for this interface
        ips: list[str] = []
        for snic in snic_list:
            is_ipv4 = (
                snic.family.name == 'AF_INET'
                if hasattr(snic.family, 'name')
                else snic.family == socket.AF_INET
            )
            if is_ipv4 and snic.address:
                ips.append(snic.address)

        # Create one combo item per IP address
        for ip in ips:
            choices.append(f"{iface_name} - {ip}")

    if not choices:
        logger.warning("No physical NIC found")
        choices.append("(未检测到网卡)")

    return choices


def get_nic_display_list() -> list[tuple[str, str]]:
    """Enumerate physical NICs and return (display_name, first_ip) tuples.

    Unlike get_nic_choices(), this returns structured data for programmatic
    use, where each entry contains the base interface name and its primary
    IPv4 address.

    Returns:
        List of (interface_name, first_ipv4) tuples.
    """
    logger = get_logger(__name__)
    result: list[tuple[str, str]] = []

    try:
        import psutil
        addrs = psutil.net_if_addrs()
    except ImportError:
        return result

    for iface_name, snic_list in addrs.items():
        if not is_physical_nic(iface_name):
            continue

        for snic in snic_list:
            is_ipv4 = (
                snic.family.name == 'AF_INET'
                if hasattr(snic.family, 'name')
                else snic.family == socket.AF_INET
            )
            if is_ipv4 and snic.address:
                result.append((iface_name, snic.address))
                break  # One entry per interface

    return result
