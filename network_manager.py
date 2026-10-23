#!/usr/bin/env python3
"""
network_manager.py
=================================================================================
IP-MAC Address Management & ARP/DHCP Network Simulation System
Course:  Computer Networks (702AI0C007) - MPSTME / NMIMS
Team:    Ananya, Krishna, Siddhant (Group 12)
Faculty: Prof. Asha Rawat
=================================================================================
Core Network Management Engine:
- Centralized IP-MAC SQLite Database
- ARP Resolution Workflow Simulator (Broadcast & Unicast, Cache Aging, Gratuitous ARP)
- RARP (Reverse Address Resolution) Concept Simulator
- Dynamic DHCP Allocation Engine (DORA Protocol State Machine & Reservations)
- Cisco IOS Configuration Exporter & Conflict Detector
=================================================================================
"""

import datetime
import ipaddress
import json
import re
import sqlite3
import time
from typing import Dict, List, Optional, Tuple


def normalize_mac(mac: str) -> str:
    """Normalize any MAC address format (0002.1664.0010, 00:02:16:64:00:10, 00-02-16-64-00-10) to XX:XX:XX:XX:XX:XX."""
    cleaned = re.sub(r'[^0-9a-fA-F]', '', mac.strip())
    if len(cleaned) != 12:
        raise ValueError(f"Invalid MAC address '{mac}': must have 12 hexadecimal characters.")
    return ':'.join(cleaned[i:i+2].upper() for i in range(0, 12, 2))


def format_cisco_mac(mac: str) -> str:
    """Format MAC to Cisco dotted notation: xxxx.xxxx.xxxx."""
    cleaned = re.sub(r'[^0-9a-fA-F]', '', mac.strip()).lower()
    return f"{cleaned[0:4]}.{cleaned[4:8]}.{cleaned[8:12]}"


class IPMACDatabase:
    """Centralized database storing and validating IP-to-MAC mappings."""

    def __init__(self, db_path: str = "ip_mac_management.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_mac_mappings (
                ip_address TEXT PRIMARY KEY,
                mac_address TEXT NOT NULL UNIQUE,
                hostname TEXT NOT NULL,
                subnet TEXT NOT NULL,
                vlan_id INTEGER NOT NULL DEFAULT 10,
                allocation_type TEXT NOT NULL, -- STATIC, DYNAMIC_DHCP, RESERVED_RARP
                status TEXT NOT NULL,          -- ACTIVE, EXPIRED, RELEASED, CONFLICT
                lease_start TEXT,
                lease_duration_sec INTEGER DEFAULT 604800,
                lease_expiry TEXT,
                last_seen TEXT
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL
            );
            """)
            conn.commit()

        # Seed with initial project devices if table is empty
        self._seed_initial_data()

    def _log(self, event_type: str, details: str):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            conn.execute("INSERT INTO audit_logs (timestamp, event_type, details) VALUES (?, ?, ?)",
                         (now, event_type, details))
            conn.commit()

    def _seed_initial_data(self):
        if len(self.get_all()) == 0:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            initial_devices = [
                ("192.168.10.1", "00:01:96:00:00:10", "Core-Gateway-VLAN10", "192.168.10.0/24", 10, "STATIC", "ACTIVE", None, 0, None, now),
                ("192.168.20.1", "00:01:96:00:00:20", "Core-Gateway-VLAN20", "192.168.20.0/24", 20, "STATIC", "ACTIVE", None, 0, None, now),
                ("192.168.10.15", "00:02:16:64:00:30", "PC3_Static_Admin", "192.168.10.0/24", 10, "STATIC", "ACTIVE", None, 0, None, now),
                ("192.168.10.50", "00:02:16:64:00:40", "PC4_Reserved_RARP", "192.168.10.0/24", 10, "RESERVED_RARP", "ACTIVE", now, 604800, "2026-10-28 12:00:00", now),
                ("192.168.10.21", "00:02:16:64:00:10", "PC1_Dynamic_DeptA", "192.168.10.0/24", 10, "DYNAMIC_DHCP", "ACTIVE", now, 604800, "2026-10-28 12:00:00", now),
                ("192.168.10.22", "00:02:16:64:00:20", "PC2_Dynamic_DeptA", "192.168.10.0/24", 10, "DYNAMIC_DHCP", "ACTIVE", now, 604800, "2026-10-28 12:00:00", now),
                ("192.168.20.21", "00:02:16:64:00:50", "PC5_Remote_DeptB", "192.168.20.0/24", 20, "DYNAMIC_DHCP", "ACTIVE", now, 604800, "2026-10-28 12:00:00", now),
            ]
            with self._get_connection() as conn:
                for d in initial_devices:
                    conn.execute("""
                    INSERT OR IGNORE INTO ip_mac_mappings 
                    (ip_address, mac_address, hostname, subnet, vlan_id, allocation_type, status, lease_start, lease_duration_sec, lease_expiry, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, d)
                conn.commit()
            self._log("SYSTEM_INIT", "Database initialized with default project topology nodes.")

    def add_or_update_mapping(self, ip: str, mac: str, hostname: str, subnet: str = "192.168.10.0/24",
                              vlan_id: int = 10, allocation_type: str = "STATIC", status: str = "ACTIVE",
                              lease_sec: int = 604800) -> Dict[str, str]:
        # Validate IP
        try:
            ipaddress.IPv4Address(ip.strip())
        except Exception:
            raise ValueError(f"Invalid IPv4 address: '{ip}'")

        # Validate & normalize MAC
        norm_mac = normalize_mac(mac)

        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        expiry_str = (now + datetime.timedelta(seconds=lease_sec)).strftime("%Y-%m-%d %H:%M:%S") if lease_sec > 0 else None

        # Conflict check
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if MAC assigned to different IP
            cursor.execute("SELECT ip_address, hostname FROM ip_mac_mappings WHERE mac_address = ? AND ip_address != ?", (norm_mac, ip.strip()))
            conflict_mac = cursor.fetchone()
            if conflict_mac:
                self._log("CONFLICT_WARNING", f"MAC {norm_mac} was previously bound to {conflict_mac['ip_address']} ({conflict_mac['hostname']}). Updating binding.")

            cursor.execute("""
            INSERT INTO ip_mac_mappings (ip_address, mac_address, hostname, subnet, vlan_id, allocation_type, status, lease_start, lease_duration_sec, lease_expiry, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ip_address) DO UPDATE SET
                mac_address=excluded.mac_address,
                hostname=excluded.hostname,
                subnet=excluded.subnet,
                vlan_id=excluded.vlan_id,
                allocation_type=excluded.allocation_type,
                status=excluded.status,
                lease_start=excluded.lease_start,
                lease_duration_sec=excluded.lease_duration_sec,
                lease_expiry=excluded.lease_expiry,
                last_seen=excluded.last_seen;
            """, (ip.strip(), norm_mac, hostname.strip(), subnet.strip(), vlan_id, allocation_type, status, now_str, lease_sec, expiry_str, now_str))
            conn.commit()

        self._log("MAPPING_SAVED", f"Saved {ip} -> {norm_mac} ({hostname}) Type={allocation_type}")
        return {"status": "SUCCESS", "ip": ip, "mac": norm_mac, "hostname": hostname}

    def delete_mapping(self, ip: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ip_mac_mappings WHERE ip_address = ?", (ip.strip(),))
            deleted = cursor.rowcount > 0
            conn.commit()
        if deleted:
            self._log("MAPPING_DELETED", f"Deleted mapping for IP {ip}")
        return deleted

    def lookup_ip(self, ip: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ip_mac_mappings WHERE ip_address = ?", (ip.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def lookup_mac(self, mac: str) -> Optional[Dict]:
        norm_mac = normalize_mac(mac)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ip_mac_mappings WHERE mac_address = ?", (norm_mac,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ip_mac_mappings ORDER BY vlan_id ASC, ip_address ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def generate_cisco_ios_commands(self) -> str:
        """Export the database mappings as valid Cisco IOS configuration commands."""
        lines = [
            "!",
            "! ===================================================================",
            "! CISCO IOS CONFIGURATION GENERATED FROM IP-MAC MANAGEMENT SYSTEM",
            "! Topic: IP-MAC Address Management & ARP/DHCP Network Simulation",
            "! Team: Ananya, Krishna, Siddhant | Course: Computer Networks",
            "! ===================================================================",
            "configure terminal",
            "!",
            "! --- 1. DHCP EXCLUSIONS ---",
            "ip dhcp excluded-address 192.168.10.1 192.168.10.20",
            "ip dhcp excluded-address 192.168.20.1 192.168.20.20",
            "!",
            "! --- 2. STATIC ARP ENTRIES (High-Security IP-MAC Binding) ---",
        ]

        records = self.get_all()
        for r in records:
            if r['allocation_type'] == 'STATIC' and not r['hostname'].startswith('Core-Gateway'):
                cisco_mac = format_cisco_mac(r['mac_address'])
                lines.append(f"arp {r['ip_address']} {cisco_mac} arpa")

        lines.extend([
            "!",
            "! --- 3. DYNAMIC DHCP POOLS ---",
            "ip dhcp pool POOL_DEPT_A",
            " network 192.168.10.0 255.255.255.0",
            " default-router 192.168.10.1",
            " dns-server 192.168.10.1",
            " lease 7 0 0",
            " exit",
            "!",
            "ip dhcp pool POOL_DEPT_B",
            " network 192.168.20.0 255.255.255.0",
            " default-router 192.168.20.1",
            " dns-server 192.168.10.1",
            " lease 7 0 0",
            " exit",
            "!",
            "! --- 4. STATIC DHCP RESERVATIONS (RARP CONCEPT) ---",
        ])

        for r in records:
            if r['allocation_type'] == 'RESERVED_RARP':
                raw_mac = re.sub(r'[^0-9a-fA-F]', '', r['mac_address']).lower()
                cisco_client_id = f"01{raw_mac[0:2]}.{raw_mac[2:6]}.{raw_mac[6:10]}.{raw_mac[10:12]}"
                pool_name = f"RES_{r['hostname'].replace('-', '_').upper()}"
                lines.extend([
                    f"ip dhcp pool {pool_name}",
                    f" host {r['ip_address']} 255.255.255.0",
                    f" client-identifier {cisco_client_id}",
                    " default-router 192.168.10.1",
                    " dns-server 192.168.10.1",
                    " exit",
                    "!",
                ])

        lines.extend([
            "end",
            "write memory",
            "!",
        ])
        return "\n".join(lines)


class ARPSimulator:
    """Simulates Address Resolution Protocol (ARP) workflow."""

    def __init__(self, db: IPMACDatabase):
        self.db = db
        # Host local ARP caches: host_name -> dict(ip -> {mac, age_sec, type})
        self.host_caches: Dict[str, Dict[str, Dict]] = {}

    def get_cache(self, hostname: str) -> Dict[str, Dict]:
        if hostname not in self.host_caches:
            self.host_caches[hostname] = {}
        return self.host_caches[hostname]

    def clear_cache(self, hostname: str):
        self.host_caches[hostname] = {}

    def simulate_resolution(self, source_hostname: str, target_ip: str) -> Dict:
        """Simulate ARP resolution step-by-step from source host to target IP."""
        trace = []
        cache = self.get_cache(source_hostname)

        # 1. Lookup source host info
        all_records = {r['hostname']: r for r in self.db.get_all()}
        source = all_records.get(source_hostname)
        if not source:
            raise ValueError(f"Source host '{source_hostname}' not found in database.")

        source_ip = source['ip_address']
        source_mac = source['mac_address']
        source_subnet = ipaddress.IPv4Network(source['subnet'], strict=False)

        trace.append({
            "step": 1,
            "title": "Local ARP Cache Lookup",
            "details": f"[{source_hostname}] checks internal ARP cache table for IP {target_ip}...",
            "status": "CHECKING"
        })

        if target_ip in cache:
            resolved_mac = cache[target_ip]['mac']
            trace.append({
                "step": 2,
                "title": "ARP Cache Hit",
                "details": f"CACHE HIT! IP {target_ip} is already mapped to MAC {resolved_mac}. No broadcast needed.",
                "packet": None,
                "status": "SUCCESS"
            })
            return {"resolved": True, "target_ip": target_ip, "mac": resolved_mac, "cache_hit": True, "trace": trace}

        trace.append({
            "step": 2,
            "title": "ARP Cache Miss & Subnet Evaluation",
            "details": f"CACHE MISS. Target IP {target_ip} is not in cache.",
            "status": "PROCESSING"
        })

        # Check if target is on same subnet or remote
        target_obj = ipaddress.IPv4Address(target_ip)
        is_local = target_obj in source_subnet

        actual_arp_target_ip = target_ip
        if not is_local:
            gateway_ip = "192.168.10.1" if source['vlan_id'] == 10 else "192.168.20.1"
            trace.append({
                "step": 3,
                "title": "Inter-Subnet Routing Detected (Default Gateway ARP)",
                "details": f"Target {target_ip} is outside local subnet {source_subnet}. Host must send frame to Default Gateway ({gateway_ip}). Initiating ARP resolution for GATEWAY {gateway_ip}!",
                "status": "ROUTING"
            })
            actual_arp_target_ip = gateway_ip

        # 3. Create ARP Request Broadcast
        arp_request_packet = {
            "Layer 2 Header": {
                "Source MAC": source_mac,
                "Destination MAC": "FF:FF:FF:FF:FF:FF (Broadcast)",
                "EtherType": "0x0806 (ARP)"
            },
            "ARP Payload": {
                "Hardware Type": "Ethernet (1)",
                "Protocol Type": "IPv4 (0x0800)",
                "Hardware Size": "6 bytes",
                "Protocol Size": "4 bytes",
                "Opcode": "1 (ARP REQUEST)",
                "Sender MAC": source_mac,
                "Sender IP": source_ip,
                "Target MAC": "00:00:00:00:00:00 (Unknown)",
                "Target IP": actual_arp_target_ip
            }
        }

        trace.append({
            "step": 4,
            "title": "ARP Request Generated (Layer 2 Broadcast)",
            "details": f"[{source_hostname}] broadcasts: 'Who has {actual_arp_target_ip}? Tell {source_ip}' to FF:FF:FF:FF:FF:FF.",
            "packet": arp_request_packet,
            "status": "BROADCAST"
        })

        # 4. Switch floods frame, destination receives
        target_record = self.db.lookup_ip(actual_arp_target_ip)
        if not target_record:
            trace.append({
                "step": 5,
                "title": "ARP Request Timeout / Host Unreachable",
                "details": f"No device in network responded to ARP request for {actual_arp_target_ip}. Request timed out.",
                "packet": None,
                "status": "FAILED"
            })
            return {"resolved": False, "target_ip": target_ip, "mac": None, "cache_hit": False, "trace": trace}

        target_name = target_record['hostname']
        target_mac = target_record['mac_address']

        trace.append({
            "step": 5,
            "title": "Target Receives & Validates Target IP",
            "details": f"Switch floods frame to all ports. [{target_name}] matches Target IP {actual_arp_target_ip}. All other devices drop the packet silently.",
            "status": "PROCESSING"
        })

        # 5. Target sends Unicast ARP Reply
        arp_reply_packet = {
            "Layer 2 Header": {
                "Source MAC": target_mac,
                "Destination MAC": source_mac,
                "EtherType": "0x0806 (ARP)"
            },
            "ARP Payload": {
                "Hardware Type": "Ethernet (1)",
                "Protocol Type": "IPv4 (0x0800)",
                "Opcode": "2 (ARP REPLY)",
                "Sender MAC": target_mac,
                "Sender IP": actual_arp_target_ip,
                "Target MAC": source_mac,
                "Target IP": source_ip
            }
        }

        trace.append({
            "step": 6,
            "title": "ARP Reply Generated (Layer 2 Unicast)",
            "details": f"[{target_name}] replies directly to [{source_hostname}] ({source_mac}): '{actual_arp_target_ip} is at {target_mac}'.",
            "packet": arp_reply_packet,
            "status": "UNICAST"
        })

        # 6. Source updates ARP cache
        cache[actual_arp_target_ip] = {
            "mac": target_mac,
            "hostname": target_name,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "type": "DYNAMIC"
        }

        trace.append({
            "step": 7,
            "title": "ARP Cache Table Updated",
            "details": f"[{source_hostname}] caches entry: {actual_arp_target_ip} -> {target_mac}. Ready to transmit IP packets!",
            "status": "SUCCESS"
        })

        return {
            "resolved": True,
            "target_ip": target_ip,
            "actual_arp_target": actual_arp_target_ip,
            "mac": target_mac,
            "cache_hit": False,
            "trace": trace
        }

    def simulate_gratuitous_arp(self, hostname: str) -> Dict:
        """Simulate Gratuitous ARP to detect IP conflicts and announce presence."""
        all_records = {r['hostname']: r for r in self.db.get_all()}
        source = all_records.get(hostname)
        if not source:
            raise ValueError(f"Host '{hostname}' not found.")

        ip = source['ip_address']
        mac = source['mac_address']

        packet = {
            "Layer 2 Header": {
                "Source MAC": mac,
                "Destination MAC": "FF:FF:FF:FF:FF:FF (Broadcast)",
                "EtherType": "0x0806 (ARP)"
            },
            "Gratuitous ARP Payload": {
                "Opcode": "1 (REQUEST) or 2 (REPLY)",
                "Sender MAC": mac,
                "Sender IP": ip,
                "Target MAC": "FF:FF:FF:FF:FF:FF",
                "Target IP": ip,
                "Purpose": "Duplicate IP Address Detection & ARP Cache Refresh across all network switches/hosts"
            }
        }
        return {
            "hostname": hostname,
            "ip": ip,
            "mac": mac,
            "packet": packet,
            "result": "No duplicate IP detected on network. IP address is safe to use."
        }


class RARPSimulator:
    """Simulates the Reverse Address Resolution Protocol (RARP) concept."""

    def __init__(self, db: IPMACDatabase):
        self.db = db

    def query_rarp(self, client_mac: str) -> Dict:
        norm_mac = normalize_mac(client_mac)
        record = self.db.lookup_mac(norm_mac)

        request_packet = {
            "Layer 2 Header": {
                "Source MAC": norm_mac,
                "Destination MAC": "FF:FF:FF:FF:FF:FF (Broadcast)",
                "EtherType": "0x8035 (RARP)"
            },
            "RARP Payload": {
                "Hardware Type": "Ethernet (1)",
                "Protocol Type": "IPv4 (0x0800)",
                "Opcode": "3 (RARP REQUEST)",
                "Sender MAC": norm_mac,
                "Sender IP": "0.0.0.0 (Unknown to client)",
                "Target MAC": norm_mac,
                "Target IP": "0.0.0.0 (Requesting assigned IP)"
            }
        }

        if not record:
            return {
                "success": False,
                "mac": norm_mac,
                "request_packet": request_packet,
                "reply_packet": None,
                "explanation": f"RARP Server has NO entry for hardware MAC {norm_mac}. Host cannot boot without static IP-MAC mapping in server database."
            }

        assigned_ip = record['ip_address']
        reply_packet = {
            "Layer 2 Header": {
                "Source MAC": "00:01:96:00:00:10 (RARP Server / Gateway)",
                "Destination MAC": norm_mac,
                "EtherType": "0x8035 (RARP)"
            },
            "RARP Payload": {
                "Opcode": "4 (RARP REPLY)",
                "Sender MAC": "00:01:96:00:00:10",
                "Sender IP": "192.168.10.1",
                "Target MAC": norm_mac,
                "Target IP": assigned_ip
            }
        }

        return {
            "success": True,
            "mac": norm_mac,
            "assigned_ip": assigned_ip,
            "hostname": record['hostname'],
            "request_packet": request_packet,
            "reply_packet": reply_packet,
            "explanation": (
                f"RARP Server matched MAC {norm_mac} to {assigned_ip} ({record['hostname']}). "
                "Note: RARP only provides the IP address. It cannot supply subnet masks, default gateways, or DNS. "
                "Because of this, RARP was superseded by BOOTP and subsequently modern DHCP."
            )
        }


class DHCPSimulator:
    """Simulates Dynamic Host Configuration Protocol (DHCP) DORA workflow."""

    def __init__(self, db: IPMACDatabase):
        self.db = db

    def simulate_dora(self, client_hostname: str, client_mac: str, vlan_id: int = 10) -> Dict:
        norm_mac = normalize_mac(client_mac)
        steps = []

        # 1. Check for Static Reservation (Modern RARP equivalent)
        existing = self.db.lookup_mac(norm_mac)
        is_reserved = existing and existing['allocation_type'] == 'RESERVED_RARP'

        if is_reserved:
            offered_ip = existing['ip_address']
            alloc_type = "RESERVED_RARP"
        else:
            # Pick next available IP from pool
            all_ips = {r['ip_address'] for r in self.db.get_all()}
            prefix = "192.168.10." if vlan_id == 10 else "192.168.20."
            offered_ip = None
            for host_num in range(21, 250):
                candidate = f"{prefix}{host_num}"
                if candidate not in all_ips:
                    offered_ip = candidate
                    break
            alloc_type = "DYNAMIC_DHCP"

        gateway_ip = "192.168.10.1" if vlan_id == 10 else "192.168.20.1"

        # Step 1: DHCP DISCOVER
        discover_pkt = {
            "Protocol": "UDP (Client Port 68 -> Server Port 67)",
            "IP Header": "Source: 0.0.0.0 -> Destination: 255.255.255.255 (Broadcast)",
            "DHCP Header": {
                "Opcode": "1 (BOOTREQUEST)",
                "Transaction ID (XID)": "0x39A4F2C1",
                "Client IP (ciaddr)": "0.0.0.0",
                "Your IP (yiaddr)": "0.0.0.0",
                "Client Hardware Addr (chaddr)": norm_mac,
                "Option 53": "DHCP Discover"
            }
        }
        steps.append({
            "step": "D",
            "name": "DHCP DISCOVER",
            "from": client_hostname,
            "to": "DHCP Server (Broadcast)",
            "desc": f"Client broadcasts to 255.255.255.255 seeking any available DHCP server. Provides MAC {norm_mac}.",
            "packet": discover_pkt
        })

        # Step 2: DHCP OFFER
        offer_pkt = {
            "Protocol": "UDP (Server Port 67 -> Client Port 68)",
            "IP Header": f"Source: {gateway_ip} -> Destination: 255.255.255.255",
            "DHCP Header": {
                "Opcode": "2 (BOOTREPLY)",
                "Transaction ID (XID)": "0x39A4F2C1",
                "Your IP (yiaddr)": offered_ip,
                "Option 53": "DHCP Offer",
                "Option 1 (Subnet Mask)": "255.255.255.0",
                "Option 3 (Default Router)": gateway_ip,
                "Option 6 (DNS Server)": "192.168.10.1",
                "Option 51 (Lease Time)": "604800 seconds (7 Days)",
                "Option 54 (Server Identifier)": gateway_ip
            }
        }
        steps.append({
            "step": "O",
            "name": "DHCP OFFER",
            "from": "Core-Gateway (DHCP Server)",
            "to": client_hostname,
            "desc": f"Server reserves {offered_ip} and offers it to client along with subnet mask, gateway, DNS, and lease time.",
            "packet": offer_pkt
        })

        # Step 3: DHCP REQUEST
        request_pkt = {
            "Protocol": "UDP (Client Port 68 -> Server Port 67)",
            "IP Header": "Source: 0.0.0.0 -> Destination: 255.255.255.255",
            "DHCP Header": {
                "Opcode": "1 (BOOTREQUEST)",
                "Transaction ID (XID)": "0x39A4F2C1",
                "Option 53": "DHCP Request",
                "Option 50 (Requested IP)": offered_ip,
                "Option 54 (Server Identifier)": gateway_ip
            }
        }
        steps.append({
            "step": "R",
            "name": "DHCP REQUEST",
            "from": client_hostname,
            "to": "Core-Gateway (DHCP Server)",
            "desc": f"Client broadcasts acceptance of IP {offered_ip} from server {gateway_ip}.",
            "packet": request_pkt
        })

        # Step 4: DHCP ACKNOWLEDGE
        ack_pkt = {
            "Protocol": "UDP (Server Port 67 -> Client Port 68)",
            "IP Header": f"Source: {gateway_ip} -> Destination: 255.255.255.255",
            "DHCP Header": {
                "Opcode": "2 (BOOTREPLY)",
                "Transaction ID (XID)": "0x39A4F2C1",
                "Your IP (yiaddr)": offered_ip,
                "Option 53": "DHCP ACK",
                "Status": "Lease Committed to IP-MAC Database"
            }
        }
        steps.append({
            "step": "A",
            "name": "DHCP ACKNOWLEDGE",
            "from": "Core-Gateway (DHCP Server)",
            "to": client_hostname,
            "desc": f"Server finalizes lease, records binding {offered_ip} <-> {norm_mac} in database, and acknowledges client.",
            "packet": ack_pkt
        })

        # Update Database
        self.db.add_or_update_mapping(
            ip=offered_ip,
            mac=norm_mac,
            hostname=client_hostname,
            subnet=f"192.168.{vlan_id}.0/24",
            vlan_id=vlan_id,
            allocation_type=alloc_type,
            status="ACTIVE",
            lease_sec=604800
        )

        return {
            "success": True,
            "hostname": client_hostname,
            "mac": norm_mac,
            "allocated_ip": offered_ip,
            "allocation_type": alloc_type,
            "is_reserved": is_reserved,
            "steps": steps
        }


def print_cli_menu():
    db = IPMACDatabase()
    arp = ARPSimulator(db)
    rarp = RARPSimulator(db)
    dhcp = DHCPSimulator(db)

    while True:
        print("\n" + "="*70)
        print("  IP-MAC ADDRESS MANAGEMENT & ARP/DHCP SIMULATION SYSTEM")
        print("  Team: Ananya, Krishna, Siddhant | MPSTME Computer Networks")
        print("="*70)
        print("  1. Display All IP-MAC Mappings (Database)")
        print("  2. Simulate ARP Workflow (Address Resolution)")
        print("  3. Simulate Gratuitous ARP (Duplicate IP Detection)")
        print("  4. Simulate RARP Workflow (Hardware MAC -> IP)")
        print("  5. Simulate DHCP DORA Process (Dynamic IP Allocation)")
        print("  6. Export Cisco IOS Configuration Script")
        print("  7. Add / Update IP-MAC Mapping")
        print("  8. Delete IP-MAC Mapping")
        print("  9. View System Audit Logs")
        print("  0. Exit")
        print("="*70)

        choice = input("Enter choice [0-9]: ").strip()
        if choice == '1':
            records = db.get_all()
            print(f"\n{'IP Address':<16} {'MAC Address':<20} {'Hostname':<22} {'VLAN':<6} {'Type':<14} {'Status':<10}")
            print("-" * 90)
            for r in records:
                print(f"{r['ip_address']:<16} {r['mac_address']:<20} {r['hostname']:<22} {r['vlan_id']:<6} {r['allocation_type']:<14} {r['status']:<10}")
        elif choice == '2':
            records = db.get_all()
            hosts = [r['hostname'] for r in records if not r['hostname'].startswith('Core-Gateway')]
            print("\nAvailable Hosts:")
            for i, h in enumerate(hosts):
                print(f"  {i+1}. {h}")
            src_idx = int(input("Select Source Host number: ")) - 1
            src_host = hosts[src_idx]
            target_ip = input("Enter Target IP to resolve (e.g. 192.168.10.15 or 192.168.20.21): ").strip()
            res = arp.simulate_resolution(src_host, target_ip)
            print("\n--- ARP WORKFLOW TRACE ---")
            for t in res['trace']:
                print(f"Step {t['step']}: {t['title']} -> {t['details']}")
            if res['resolved']:
                print(f"\n=> RESULT: IP {target_ip} resolved to MAC: {res['mac']}")
        elif choice == '3':
            host = input("Enter Hostname for Gratuitous ARP (e.g. PC1_Dynamic_DeptA): ").strip()
            res = arp.simulate_gratuitous_arp(host)
            print("\nGratuitous ARP Output:")
            print(json.dumps(res, indent=2))
        elif choice == '4':
            mac = input("Enter Client MAC Address (e.g. 00:02:16:64:00:40): ").strip()
            res = rarp.query_rarp(mac)
            print("\n--- RARP WORKFLOW RESULT ---")
            print(f"Success: {res['success']}")
            if res['success']:
                print(f"Assigned IP: {res['assigned_ip']} ({res['hostname']})")
            print(f"Explanation: {res['explanation']}")
        elif choice == '5':
            hname = input("Enter Client Hostname (e.g. NewLaptop): ").strip()
            mac = input("Enter Client MAC (e.g. 00:02:16:64:00:99): ").strip()
            res = dhcp.simulate_dora(hname, mac, vlan_id=10)
            print("\n--- DHCP DORA TRANSACTION TRACE ---")
            for s in res['steps']:
                print(f"[{s['step']}] {s['name']}: {s['from']} -> {s['to']}")
                print(f"    {s['desc']}")
            print(f"\n=> FINAL ALLOCATION: IP {res['allocated_ip']} allocated to {hname} ({res['mac']})")
        elif choice == '6':
            print("\n" + db.generate_cisco_ios_commands())
        elif choice == '7':
            ip = input("IP: ").strip()
            mac = input("MAC: ").strip()
            hname = input("Hostname: ").strip()
            atype = input("Type [STATIC/DYNAMIC_DHCP/RESERVED_RARP]: ").strip().upper() or "STATIC"
            db.add_or_update_mapping(ip, mac, hname, allocation_type=atype)
            print("[+] Saved successfully!")
        elif choice == '8':
            ip = input("Enter IP to delete: ").strip()
            db.delete_mapping(ip)
            print("[+] Deleted!")
        elif choice == '9':
            logs = db.get_audit_logs()
            for l in logs:
                print(f"[{l['timestamp']}] {l['event_type']}: {l['details']}")
        elif choice == '0':
            print("Exiting...")
            break


if __name__ == '__main__':
    print_cli_menu()
