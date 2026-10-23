#!/usr/bin/env python3
"""
generate_pkt.py
---------------------------------------------------------------------------------
Project: IP-MAC Address Management and ARP/DHCP Network Simulation System
Course:  Computer Networks (702AI0C007) - MPSTME / NMIMS
Team:    Ananya, Krishna, Siddhant (Group 12)
Faculty: Prof. Asha Rawat
---------------------------------------------------------------------------------
Generates a complete, native Cisco Packet Tracer (.pkt) simulation file
with fully functional Layer 3 Core Gateway, Access Switch, and PCs.
"""

import os
import sys
import uuid
import zlib
import xml.etree.ElementTree as ET

# Cisco IOS Running & Startup Config for Core-Gateway (Catalyst 3650 L3 Switch/Router)
CORE_GATEWAY_CONFIG = """!
version 16.3.2
no service timestamps log datetime msec
no service timestamps debug datetime msec
no service password-encryption
!
hostname Core-Gateway
!
ip routing
!
! DHCP Address Exclusions (Gateways, Static Admin, Network Infrastructure)
ip dhcp excluded-address 192.168.10.1 192.168.10.20
ip dhcp excluded-address 192.168.20.1 192.168.20.20
!
! Dynamic DHCP Pool for Dept-A (VLAN 10)
ip dhcp pool POOL_DEPT_A
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.1
 dns-server 192.168.10.1
!
! Dynamic DHCP Pool for Dept-B (VLAN 20)
ip dhcp pool POOL_DEPT_B
 network 192.168.20.0 255.255.255.0
 default-router 192.168.20.1
 dns-server 192.168.10.1
!
! Static DHCP Reservation Pool (Modern RARP Equivalent) for PC4 (MAC 0002.1664.0040)
ip dhcp pool RESERVED_RARP_PC4
 host 192.168.10.50 255.255.255.0
 client-identifier 0100.0216.6400.40
 default-router 192.168.10.1
 dns-server 192.168.10.1
!
! Static IP-MAC Database Mapping (Static ARP Entry for High-Security Admin Host PC3)
arp 192.168.10.15 0002.1664.0030 arpa
!
spanning-tree mode rapid-pvst
spanning-tree portfast default
spanning-tree vlan 1,10,20 priority 4096
!
vlan 10
 name Dept-A_Users
!
vlan 20
 name Dept-B_Remote
!
interface GigabitEthernet1/0/1
 description Trunk Link to Access-Switch
 switchport mode trunk
 switchport nonegotiate
 no shutdown
!
interface Vlan1
 no ip address
 shutdown
!
interface Vlan10
 description Default Gateway for Dept-A
 ip address 192.168.10.1 255.255.255.0
 no shutdown
!
interface Vlan20
 description Default Gateway for Dept-B
 ip address 192.168.20.1 255.255.255.0
 no shutdown
!
ip classless
!
line con 0
line vty 0 4
 login
!
end
"""

# Cisco IOS Running & Startup Config for Access-Switch (Catalyst 3650 L2 Switch)
ACCESS_SWITCH_CONFIG = """!
version 16.3.2
no service timestamps log datetime msec
no service timestamps debug datetime msec
no service password-encryption
!
hostname Access-Switch
!
spanning-tree mode rapid-pvst
spanning-tree portfast default
spanning-tree vlan 1,10,20 priority 8192
!
vlan 10
 name Dept-A_Users
!
vlan 20
 name Dept-B_Remote
!
interface GigabitEthernet1/0/24
 description Trunk Link to Core-Gateway
 switchport mode trunk
 switchport nonegotiate
 no shutdown
!
interface GigabitEthernet1/0/1
 description Access Port for PC1 (Dynamic DHCP)
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
 no shutdown
!
interface GigabitEthernet1/0/2
 description Access Port for PC2 (Dynamic DHCP)
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
 no shutdown
!
interface GigabitEthernet1/0/3
 description Access Port for PC3 (Static Admin)
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
 no shutdown
!
interface GigabitEthernet1/0/4
 description Access Port for PC4 (RARP / Reserved DHCP)
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
 no shutdown
!
interface GigabitEthernet1/0/5
 description Access Port for PC5 (Dept-B Remote VLAN 20)
 switchport access vlan 20
 switchport mode access
 spanning-tree portfast
 no shutdown
!
interface Vlan1
 no ip address
 shutdown
!
line con 0
line vty 0 4
 login
!
end
"""

PC_DEFINITIONS = [
    {
        'name': 'PC1-Dynamic',
        'desc': 'Dept-A Dynamic Client 1 (DHCP DORA Demonstration)',
        'pos': (100, 450),
        'switch': 'Access-Switch',
        'switch_port': 'GigabitEthernet1/0/1',
        'dhcp': False,
        'ip': '192.168.10.21',
        'mask': '255.255.255.0',
        'gw': '192.168.10.1',
        'mac': '0002.1664.0010',
    },
    {
        'name': 'PC2-Dynamic',
        'desc': 'Dept-A Dynamic Client 2 (Intra-Subnet ARP Demonstration)',
        'pos': (300, 450),
        'switch': 'Access-Switch',
        'switch_port': 'GigabitEthernet1/0/2',
        'dhcp': False,
        'ip': '192.168.10.22',
        'mask': '255.255.255.0',
        'gw': '192.168.10.1',
        'mac': '0002.1664.0020',
    },
    {
        'name': 'PC3-Admin',
        'desc': 'Dept-A Admin Workstation (Static IP-MAC Database Mapping)',
        'pos': (500, 450),
        'switch': 'Access-Switch',
        'switch_port': 'GigabitEthernet1/0/3',
        'dhcp': False,
        'ip': '192.168.10.15',
        'mask': '255.255.255.0',
        'gw': '192.168.10.1',
        'mac': '0002.1664.0030',
    },
    {
        'name': 'PC4-Reserved',
        'desc': 'Dept-A Reserved Host (RARP / Static DHCP Reservation -> 192.168.10.50)',
        'pos': (700, 450),
        'switch': 'Access-Switch',
        'switch_port': 'GigabitEthernet1/0/4',
        'dhcp': False,
        'ip': '192.168.10.50',
        'mask': '255.255.255.0',
        'gw': '192.168.10.1',
        'mac': '0002.1664.0040',
    },
    {
        'name': 'PC5-DeptB',
        'desc': 'Dept-B Remote Client (Inter-Subnet Gateway ARP Resolution)',
        'pos': (900, 450),
        'switch': 'Access-Switch',
        'switch_port': 'GigabitEthernet1/0/5',
        'dhcp': False,
        'ip': '192.168.20.21',
        'mask': '255.255.255.0',
        'gw': '192.168.20.1',
        'mac': '0002.1664.0050',
    },
]


def _write_config_section(engine_elem, section_name, config_text):
    section = engine_elem.find(section_name)
    if section is None:
        section = ET.SubElement(engine_elem, section_name)
    section.clear()
    for line in config_text.strip('\n').splitlines():
        line_elem = ET.SubElement(section, 'LINE')
        line_elem.text = line


def encode_legacy_pkt(xml_bytes: bytes) -> bytes:
    """Encode XML using standard Cisco Packet Tracer legacy compressed & XOR format."""
    payload = len(xml_bytes).to_bytes(4, 'big') + zlib.compress(xml_bytes)
    out_data = bytearray(payload)
    length = len(out_data)
    xor_out = bytearray()
    for byte in out_data:
        xor_out.append((byte ^ length) & 0xFF)
        length -= 1
    return bytes(xor_out)


def build_simulation_project(template_xml_path='test_template.xml', output_pkt_path='IP_MAC_Address_Management_ARP_DHCP.pkt', output_xml_path='IP_MAC_Address_Management_ARP_DHCP.xml'):
    if not os.path.exists(template_xml_path):
        raise FileNotFoundError(f"Template XML '{template_xml_path}' not found!")

    tree = ET.parse(template_xml_path)
    root = tree.getroot()
    network = root.find('NETWORK')
    devices_elem = network.find('DEVICES')

    # Extract template elements
    switch_template = None
    pc_template = None
    for dev in devices_elem.findall('DEVICE'):
        dev_type = dev.findtext('ENGINE/TYPE', '').lower()
        if 'switch' in dev_type and switch_template is None:
            switch_template = dev
        elif 'pc' in dev_type and pc_template is None:
            pc_template = dev

    if switch_template is None or pc_template is None:
        raise ValueError("Could not find both switch and pc templates in template XML")

    # Clear devices, links, and template ghost notes
    devices_elem.clear()
    links_elem = network.find('LINKS')
    if links_elem is None:
        links_elem = ET.SubElement(network, 'LINKS')
    links_elem.clear()

    # Clear all floating template notes/labels
    for notes in root.iter('NOTES'):
        notes.clear()

    # Hide ugly model labels (e.g. "3650 24PS") overlapping device names
    for m in root.iter('MODELSHOWN'):
        m.text = 'false'

    device_refs = {}

    def clone_device(template, name, x, y):
        new_dev = ET.fromstring(ET.tostring(template))
        engine = new_dev.find('ENGINE')
        save_ref = engine.find('SAVE_REF_ID')
        if save_ref is None:
            save_ref = ET.SubElement(engine, 'SAVE_REF_ID')
        unique_val = uuid.uuid4().int >> 64
        ref_id = f'save-ref-id:{unique_val}'
        save_ref.text = ref_id

        engine.find('NAME').text = name
        if engine.find('SYS_NAME') is not None:
            engine.find('SYS_NAME').text = name

        for m in new_dev.iter('MODELSHOWN'):
            m.text = 'false'

        workspace = new_dev.find('WORKSPACE')
        if workspace is not None:
            logical = workspace.find('LOGICAL')
            if logical is not None:
                if logical.find('X') is not None:
                    logical.find('X').text = str(x)
                if logical.find('Y') is not None:
                    logical.find('Y').text = str(y)

        device_refs[name] = ref_id
        return new_dev

    # 1. Create Core-Gateway (Centered apex at X=500, Y=80)
    core_sw = clone_device(switch_template, 'Core-Gateway', 500, 80)
    core_engine = core_sw.find('ENGINE')
    if core_engine.find('SERIALNUMBER') is not None:
        core_engine.find('SERIALNUMBER').text = 'CAT3650-COR-GW-01'

    # Assign distinct MAC addresses to Core-Gateway ports
    for i, port in enumerate(core_sw.findall('.//PORT')):
        mac = f"0001.9600.01{i+1:02x}"
        if port.find('MACADDRESS') is not None:
            port.find('MACADDRESS').text = mac
        if port.find('BIA') is not None:
            port.find('BIA').text = mac

    # Populate hardware VLAN database on Core-Gateway
    vlans_core = core_engine.find('VLANS')
    if vlans_core is not None:
        has_10 = any(v.get('number') == '10' for v in vlans_core.findall('VLAN'))
        has_20 = any(v.get('number') == '20' for v in vlans_core.findall('VLAN'))
        if not has_10:
            ET.SubElement(vlans_core, 'VLAN', {'number': '10', 'name': 'Dept-A_Users', 'rspan': '0'})
        if not has_20:
            ET.SubElement(vlans_core, 'VLAN', {'number': '20', 'name': 'Dept-B_Remote', 'rspan': '0'})

    _write_config_section(core_engine, 'RUNNINGCONFIG', CORE_GATEWAY_CONFIG)
    _write_config_section(core_engine, 'STARTUPCONFIG', CORE_GATEWAY_CONFIG)
    devices_elem.append(core_sw)

    # 2. Create Access-Switch (Centered spine at X=500, Y=240)
    access_sw = clone_device(switch_template, 'Access-Switch', 500, 240)
    access_engine = access_sw.find('ENGINE')
    if access_engine.find('SERIALNUMBER') is not None:
        access_engine.find('SERIALNUMBER').text = 'CAT3650-ACC-SW-01'

    # Assign distinct MAC addresses to Access-Switch ports
    for i, port in enumerate(access_sw.findall('.//PORT')):
        mac = f"0001.9600.02{i+1:02x}"
        if port.find('MACADDRESS') is not None:
            port.find('MACADDRESS').text = mac
        if port.find('BIA') is not None:
            port.find('BIA').text = mac

    # Populate hardware VLAN database on Access-Switch
    vlans_access = access_engine.find('VLANS')
    if vlans_access is not None:
        has_10 = any(v.get('number') == '10' for v in vlans_access.findall('VLAN'))
        has_20 = any(v.get('number') == '20' for v in vlans_access.findall('VLAN'))
        if not has_10:
            ET.SubElement(vlans_access, 'VLAN', {'number': '10', 'name': 'Dept-A_Users', 'rspan': '0'})
        if not has_20:
            ET.SubElement(vlans_access, 'VLAN', {'number': '20', 'name': 'Dept-B_Remote', 'rspan': '0'})

    _write_config_section(access_engine, 'RUNNINGCONFIG', ACCESS_SWITCH_CONFIG)
    _write_config_section(access_engine, 'STARTUPCONFIG', ACCESS_SWITCH_CONFIG)
    devices_elem.append(access_sw)

    # 3. Create Trunk Link between Core-Gateway (Gi1/0/1) and Access-Switch (Gi1/0/24)
    # Using eCrossOver cable type for Switch-to-Switch interconnection
    trunk_link = ET.SubElement(links_elem, 'LINK')
    ET.SubElement(trunk_link, 'TYPE').text = 'eCopper'
    cable = ET.SubElement(trunk_link, 'CABLE')
    ET.SubElement(cable, 'LENGTH').text = '10'
    ET.SubElement(cable, 'FUNCTIONAL').text = 'true'
    ET.SubElement(cable, 'FROM').text = device_refs['Core-Gateway']
    ET.SubElement(cable, 'PORT').text = 'GigabitEthernet1/0/1'
    ET.SubElement(cable, 'TO').text = device_refs['Access-Switch']
    ET.SubElement(cable, 'PORT').text = 'GigabitEthernet1/0/24'
    ET.SubElement(cable, 'TYPE').text = 'eCrossOver'

    # 4. Create PCs and Links
    for idx, pc_def in enumerate(PC_DEFINITIONS):
        name = pc_def['name']
        x, y = pc_def['pos']
        pc_elem = clone_device(pc_template, name, x, y)
        pc_engine = pc_elem.find('ENGINE')

        # Set PC OS Gateway and DNS
        if pc_engine.find('SERIALNUMBER') is not None:
            pc_engine.find('SERIALNUMBER').text = f"PTT0810-PC{idx+1}-"
        if pc_engine.find('GATEWAY') is not None:
            pc_engine.find('GATEWAY').text = pc_def['gw']
        dns_client = pc_engine.find('DNS_CLIENT')
        if dns_client is not None:
            server_ip = dns_client.find('SERVER_IP')
            if server_ip is not None:
                server_ip.text = '192.168.10.1'

        # Ensure FastEthernet0 is registered in DHCP_CLIENT if present
        dhcp_client = pc_engine.find('DHCP_CLIENT')
        if dhcp_client is not None:
            port_data_map = dhcp_client.find('PORT_DATA_MAP')
            if port_data_map is not None:
                has_fa0 = any(p.findtext('PORT') == 'FastEthernet0' for p in port_data_map.findall('PORT_DATA_ENTRY'))
                if not has_fa0:
                    entry = ET.SubElement(port_data_map, 'PORT_DATA_ENTRY')
                    ET.SubElement(entry, 'PORT').text = 'FastEthernet0'

        # Configure only Ethernet port settings
        for port in pc_elem.findall('.//PORT'):
            if port.findtext('TYPE') == 'eCopperFastEthernet':
                if port.find('MACADDRESS') is not None:
                    port.find('MACADDRESS').text = pc_def['mac']
                if port.find('BIA') is not None:
                    port.find('BIA').text = pc_def['mac']
                if port.find('PORT_DHCP_ENABLE') is not None:
                    port.find('PORT_DHCP_ENABLE').text = 'true' if pc_def['dhcp'] else 'false'
                if port.find('IP') is not None:
                    port.find('IP').text = pc_def['ip']
                if port.find('SUBNET') is not None:
                    port.find('SUBNET').text = pc_def['mask']
                if port.find('PORT_GATEWAY') is not None:
                    port.find('PORT_GATEWAY').text = pc_def['gw']
                if port.find('PORT_DNS') is not None:
                    port.find('PORT_DNS').text = '192.168.10.1'

        devices_elem.append(pc_elem)

        # Add link to switch (Straight-Through for PC to Switch)
        pc_link = ET.SubElement(links_elem, 'LINK')
        ET.SubElement(pc_link, 'TYPE').text = 'eCopper'
        c = ET.SubElement(pc_link, 'CABLE')
        ET.SubElement(c, 'LENGTH').text = '5'
        ET.SubElement(c, 'FUNCTIONAL').text = 'true'
        ET.SubElement(c, 'FROM').text = device_refs[name]
        ET.SubElement(c, 'PORT').text = 'FastEthernet0'
        ET.SubElement(c, 'TO').text = device_refs[pc_def['switch']]
        ET.SubElement(c, 'PORT').text = pc_def['switch_port']
        ET.SubElement(c, 'TYPE').text = 'eStraightThrough'

    # Save XML
    ET.indent(tree, space=' ')
    tree.write(output_xml_path, encoding='utf-8', xml_declaration=False)
    print(f"[+] Packet Tracer XML generated: {output_xml_path}")

    # Encode to PKT
    with open(output_xml_path, 'rb') as f:
        xml_bytes = f.read()

    pkt_bytes = encode_legacy_pkt(xml_bytes)
    with open(output_pkt_path, 'wb') as f:
        f.write(pkt_bytes)

    print(f"[+] Native Packet Tracer file compiled successfully: {output_pkt_path} ({len(pkt_bytes)} bytes)")


if __name__ == '__main__':
    build_simulation_project()
