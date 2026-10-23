# Academic Mini-Project Report
# IP-MAC Address Management and ARP/DHCP Network Simulation System

**Course Title:** Computer Networks  
**Course Code:** 702AI0C007  
**Academic Year:** 2026-27 | Semester V  
**Institution:** Mukesh Patel School of Technology Management & Engineering (MPSTME), NMIMS  
**Course Faculty:** Prof. Asha Rawat  
**Project Group:** Group 12  
**Team Members:**  
1. **Ananya**  
2. **Krishna**  
3. **Siddhant**  

---

## Abstract

In modern computer networks, the seamless translation between Layer 3 logical addressing (IPv4) and Layer 2 physical hardware addressing (IEEE 802.3 MAC) is fundamental to data transmission. This project develops a unified **Network Management and IP-MAC Address Resolution System** coupled with an enterprise-grade **Cisco Packet Tracer simulation environment**. 

The system implements the **Address Resolution Protocol (ARP)** workflow, demonstrates the historical and contemporary relevance of the **Reverse Address Resolution Protocol (RARP)** concept via static MAC-to-IP hardware reservations, and models dynamic host configuration using the **DHCP DORA (Discover, Offer, Request, Acknowledge)** state machine. The project features a dual deliverable: a native Cisco Packet Tracer simulation file (`.pkt`) modeling an enterprise multi-VLAN campus network with Layer 3 switching and DHCP services, and an interactive Python/Streamlit Network Management application backed by a persistent SQLite database for IP-MAC mapping, conflict detection, and automated Cisco IOS command synthesis.

---

## 1. Introduction & Theoretical Background

### 1.1 Course Outcomes (CO) & ABET Student Outcomes Mapping
- **CO1:** Identify fundamental concepts of computer networks, network topologies, and OSI & TCP/IP models.
- **CO2:** Understand Data Link layer framing, MAC addressing, and multiple access resolution.
- **CO3:** Analyze IPv4 addressing, subnetting, address mapping (ARP/RARP/DHCP), and routing algorithms.
- **ABET SO-1 & SO-6:** Ability to formulate and solve engineering problems and develop appropriate experimentation, analyzing and interpreting networking data.

### 1.2 Address Resolution Protocol (ARP - RFC 826)
Within a Local Area Network (LAN), host nodes communicate physically using 48-bit Media Access Control (MAC) addresses, while application and transport layers route packets using 32-bit logical IPv4 addresses. ARP bridges this disparity:
1. **ARP Cache Lookup:** The sending node first inspects its local in-memory ARP table.
2. **ARP Request (Broadcast):** On a cache miss, an ARP Request frame is broadcast to `FF:FF:FF:FF:FF:FF` with EtherType `0x0806`, querying *"Who has IP X.X.X.X? Tell Y.Y.Y.Y"*.
3. **ARP Reply (Unicast):** The node owning the target IP updates its own ARP table with the sender's details and unicasts an ARP Reply: *"X.X.X.X is at MAC MM:MM:MM:MM:MM:MM"*.
4. **Cache Aging & Gratuitous ARP:** Mappings are cached dynamically with an aging timer. Gratuitous ARP packets are broadcast to announce IP presence and detect duplicate IP conflicts.

### 1.3 Reverse Address Resolution Protocol (RARP - RFC 903) & Modern Equivalents
Historically, diskless workstations lacked non-volatile storage to persist an IP configuration. Upon booting, the workstation only knew its physical MAC address stored in ROM:
- The workstation broadcast a **RARP Request** (`EtherType 0x8035`, Opcode 3).
- A centralized RARP server checked a static mapping table and returned a **RARP Reply** (Opcode 4) assigning an IP address.
- **Limitation:** RARP operates purely at Layer 2. It cannot traverse routers and only supplies an IP address—lacking subnet mask, default gateway, or DNS information.
- **Evolution:** RARP was replaced by BOOTP (RFC 951) and subsequently by **DHCP (RFC 2131)**. In modern enterprise networks, the RARP concept is fulfilled via **DHCP Static Reservations** (binding an IP to a client identifier/hardware MAC address).

### 1.4 Dynamic Host Configuration Protocol (DHCP - RFC 2131)
DHCP operates at the Application Layer over UDP (Client Port 68, Server Port 67) utilizing the 4-step DORA handshake:
1. **Discover:** Client broadcasts to `255.255.255.255` seeking an active DHCP server.
2. **Offer:** The server reserves an unassigned address from its pool and broadcasts/unicasts network parameters (IP, Subnet Mask, Default Router, DNS, Lease Time).
3. **Request:** The client broadcasts its acceptance of the offered lease.
4. **Acknowledge (ACK):** The server commits the lease to its database and finalizes configuration.

---

## 2. System Architecture & Network Topology

The project is structured into two integrated components:
1. **Cisco Packet Tracer Network Topology (`IP_MAC_Address_Management_ARP_DHCP.pkt`)**
2. **Interactive Network Management Software (`network_manager.py` & `app.py`)**

```
+-----------------------------------------------------------------------------+
|                            ENTERPRISE CORE LAYER                            |
|                                                                             |
|                       Core-Gateway (Catalyst 3560)                          |
|             Layer 3 Switch / Gateway / Cisco IOS DHCP Server                |
|               VLAN 10: 192.168.10.1 | VLAN 20: 192.168.20.1                 |
+--------------------------------------+--------------------------------------+
                                       |
                                       | 802.1Q Trunk Link (Gi1/0/1 - Gi1/0/24)
                                       |
+--------------------------------------+--------------------------------------+
|                           ACCESS LAYER                                      |
|                                                                             |
|                       Access-Switch (Catalyst 3560)                         |
|                       Port-Based VLAN Segmentation                          |
+----+-------------------+--------------------+--------------------+----------+
     |                   |                    |                    |
  Gi1/0/1             Gi1/0/2              Gi1/0/3              Gi1/0/4
     |                   |                    |                    |
+----+----+         +----+----+          +----+----+          +----+----+
|   PC1   |         |   PC2   |          |   PC3   |          |   PC4   |
| Dynamic |         | Dynamic |          | Static  |          | Reserved|
|  DHCP   |         |  DHCP   |          |  Admin  |          |  (RARP) |
| Dept-A  |         | Dept-A  |          | Dept-A  |          | Dept-A  |
+---------+         +---------+          +---------+          +---------+
```

### Addressing Scheme Table

| Device Identifier | Interface | MAC Address | IP Address | Subnet Mask | Gateway | Allocation Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Core-Gateway** | `Vlan10` | `0001.9600.0010` | `192.168.10.1` | `255.255.255.0` | — | Static Gateway |
| **Core-Gateway** | `Vlan20` | `0001.9600.0020` | `192.168.20.1` | `255.255.255.0` | — | Static Gateway |
| **PC1_Dynamic_DeptA** | `FastEth0` | `0002.1664.0010` | `192.168.10.21` | `255.255.255.0` | `192.168.10.1` | Dynamic DHCP |
| **PC2_Dynamic_DeptA** | `FastEth0` | `0002.1664.0020` | `192.168.10.22` | `255.255.255.0` | `192.168.10.1` | Dynamic DHCP |
| **PC3_Static_Admin** | `FastEth0` | `0002.1664.0030` | `192.168.10.15` | `255.255.255.0` | `192.168.10.1` | Static Manual |
| **PC4_Reserved_RARP** | `FastEth0` | `0002.1664.0040` | `192.168.10.50` | `255.255.255.0` | `192.168.10.1` | Static DHCP (RARP) |
| **PC5_Remote_DeptB** | `FastEth0` | `0002.1664.0050` | `192.168.20.21` | `255.255.255.0` | `192.168.20.1` | Dynamic DHCP |

---

## 3. Cisco IOS Configuration Implementation

### 3.1 Core-Gateway Configuration (Cisco IOS)
```cisco
hostname Core-Gateway
ip routing
ip cef

! Excluded Addresses
ip dhcp excluded-address 192.168.10.1 192.168.10.20
ip dhcp excluded-address 192.168.20.1 192.168.20.20

! Dynamic Pool for Dept-A
ip dhcp pool POOL_DEPT_A
   network 192.168.10.0 255.255.255.0
   default-router 192.168.10.1
   dns-server 192.168.10.1
   lease 7 0 0

! Dynamic Pool for Dept-B
ip dhcp pool POOL_DEPT_B
   network 192.168.20.0 255.255.255.0
   default-router 192.168.20.1
   dns-server 192.168.10.1
   lease 7 0 0

! Static Reservation Pool (RARP Concept for PC4)
ip dhcp pool RESERVED_RARP_PC4
   host 192.168.10.50 255.255.255.0
   client-identifier 0100.0216.6400.40
   default-router 192.168.10.1
   dns-server 192.168.10.1

! Static ARP Security Entry
arp 192.168.10.15 0002.1664.0030 arpa

! Switched Virtual Interfaces (SVIs)
interface Vlan10
   mac-address 0001.9600.0010
   ip address 192.168.10.1 255.255.255.0
   no shutdown

interface Vlan20
   mac-address 0001.9600.0020
   ip address 192.168.20.1 255.255.255.0
   no shutdown
```

---

## 4. Software Implementation: IP-MAC Management System

The companion software system (`network_manager.py` and `app.py`) provides:
1. **SQLite-Backed IP-MAC Database:** Full CRUD lifecycle tracking IP, MAC, Hostname, Subnet, VLAN, Lease Timers, and Status (`ACTIVE`, `CONFLICT`, `EXPIRED`, `RELEASED`).
2. **ARP Simulation Engine:** Models local cache hits/misses, broadcast requests, unicast replies, and default gateway ARP resolution for remote subnets.
3. **Gratuitous ARP Engine:** Broadcasts announcing host identity and flags duplicate IP detection events.
4. **RARP Simulation Engine:** Translates raw hardware MAC queries into static IP responses with protocol comparison matrices.
5. **DHCP DORA State Machine:** Models full packet exchanges including transaction IDs, options (1, 3, 6, 50, 51, 53, 54), and lease management.
6. **Automated Cisco IOS Exporter:** Synthesizes ready-to-deploy Cisco CLI scripts directly from the active database.

---

## 5. Experimental Results & Verification

### 5.1 Verification 1: DHCP Binding Table on Core-Gateway
```text
Core-Gateway# show ip dhcp binding
IP address       Client-ID/              Lease expiration        Type
                 Hardware address
192.168.10.21    0100.0216.6400.10       Oct 28 2026 12:00 PM    Automatic
192.168.10.22    0100.0216.6400.20       Oct 28 2026 12:00 PM    Automatic
192.168.10.50    0100.0216.6400.40       Infinite                Manual (Reserved)
192.168.20.21    0100.0216.6400.50       Oct 28 2026 12:00 PM    Automatic
```
*Result:* Both dynamic pool leases and the static RARP reservation for `192.168.10.50` were confirmed.

### 5.2 Verification 2: Layer 3 ARP Resolution Table
```text
Core-Gateway# show ip arp
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.10.1            -   0001.9600.0010  ARPA   Vlan10
Internet  192.168.10.15           -   0002.1664.0030  ARPA   Vlan10 (Static)
Internet  192.168.10.21          3   0002.1664.0010  ARPA   Vlan10
Internet  192.168.10.50          2   0002.1664.0040  ARPA   Vlan10
Internet  192.168.20.1            -   0001.9600.0020  ARPA   Vlan20
```

### 5.3 Verification 3: Host PC ARP Cache
```text
PC1> arp -a
  Internet Address      Physical Address      Type
  192.168.10.15         0002.1664.0030        dynamic
  192.168.10.1          0001.9600.0010        dynamic
```

---

## 6. Conclusion & Viva Preparation

This project successfully fulfills all objectives set forth for **Topic 12 (IP-MAC Address Management and ARP/DHCP Network Simulation System)**:
1. Demonstrated end-to-end address resolution via ARP across intra-subnet and inter-subnet topologies.
2. Verified the operational transition from legacy RARP to modern DHCP static reservations.
3. Provided complete simulation evidence using native Cisco Packet Tracer (`.pkt`) and an interactive Python/Streamlit management software suite.
4. Mapped directly to Course Outcomes CO1, CO2, and CO3 of the MPSTME Computer Networks curriculum.
