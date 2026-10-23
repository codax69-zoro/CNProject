# IP-MAC Address Management & ARP/DHCP Network Simulation System

[![Course](https://img.shields.io/badge/Course-Computer%20Networks%20(702AI0C007)-00bceb.svg)](https://engineering.nmims.edu/)
[![Institution](https://img.shields.io/badge/Institution-MPSTME%20%2F%20NMIMS-00dfa2.svg)](https://engineering.nmims.edu/)
[![Group](https://img.shields.io/badge/Group-12-a855f7.svg)](#academic-attribution)
[![Evaluator](https://img.shields.io/badge/Faculty-Prof.%20Asha%20Rawat-ff9a76.svg)](#academic-attribution)
[![License](https://img.shields.io/badge/Status-Verified%20%26%20Complete-success.svg)](#)

An enterprise-grade computer networking simulation and address resolution platform modeling Layer 2 (MAC) and Layer 3 (IPv4) orchestration, dynamic host configuration via the DHCP DORA state machine, static RARP hardware bindings, and address resolution across multi-VLAN campus topologies.

---

## 👥 Academic Attribution

* **Institution:** Mukesh Patel School of Technology Management & Engineering (MPSTME), NMIMS
* **Course:** Computer Networks (`702AI0C007`)
* **Semester:** V (B.Tech)
* **Faculty Evaluator:** **Prof. Asha Rawat**
* **Project Team (Group 12):**
  1. **Ananya**
  2. **Krishna**
  3. **Siddhant**

---

## 🏛️ System Architecture & Network Topology

```
           [Core-Gateway (Catalyst 3650 L3 Switch / Router / DHCP Server)]
              Vlan10: 192.168.10.1/24  |  Vlan20: 192.168.20.1/24
                                      |
                      [eCrossOver Trunk: Gi1/0/1 <--> Gi1/0/24]
                                      |
            [Access-Switch (Catalyst 3650 L2 - Rapid-PVST + PortFast)]
              /             |             |             \             \
         Gi1/0/1         Gi1/0/2       Gi1/0/3       Gi1/0/4       Gi1/0/5
            |               |             |             |             |
        [PC1-DeptA]    [PC2-DeptA]   [PC3-Admin]   [PC4-RARP]   [PC5-DeptB]
        (10.21 DHCP)   (10.22 DHCP)  (10.15 Static) (10.50 RARP) (20.21 VLAN20)
```

### Addressing Scheme Table

| Device | Interface | MAC Address | IP Address | Subnet Mask | Gateway | Role / Allocation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Core-Gateway** | `Vlan10` | `0001.9600.0010` | `192.168.10.1` | `255.255.255.0` | — | L3 Gateway & DHCP Server |
| **Core-Gateway** | `Vlan20` | `0001.9600.0020` | `192.168.20.1` | `255.255.255.0` | — | L3 Gateway for Remote Dept |
| **PC1-Dynamic** | `FastEth0` | `0002.1664.0010` | `192.168.10.21` | `255.255.255.0` | `192.168.10.1` | Dynamic DHCP (POOL_DEPT_A) |
| **PC2-Dynamic** | `FastEth0` | `0002.1664.0020` | `192.168.10.22` | `255.255.255.0` | `192.168.10.1` | Dynamic DHCP / Intra-ARP |
| **PC3-Admin** | `FastEth0` | `0002.1664.0030` | `192.168.10.15` | `255.255.255.0` | `192.168.10.1` | Static Admin (Gateway ARP Lock) |
| **PC4-Reserved** | `FastEth0` | `0002.1664.0040` | `192.168.10.50` | `255.255.255.0` | `192.168.10.1` | RARP / Static DHCP Reservation |
| **PC5-DeptB** | `FastEth0` | `0002.1664.0050` | `192.168.20.21` | `255.255.255.0` | `192.168.20.1` | Remote VLAN 20 Client |

---

## 🚀 Key Features & Deliverables

1. **Native Cisco Packet Tracer Simulation (`IP_MAC_Address_Management_ARP_DHCP.pkt`)**:
   * Complete, verified `.pkt` file compatible with Cisco Packet Tracer 8.x / 9.x.
   * Full Rapid-PVST Spanning Tree convergence with PortFast.
   * Active Cisco IOS DHCP pools (`POOL_DEPT_A`, `POOL_DEPT_B`, `RESERVED_RARP_PC4`).
   * 100% verified ping / PDU success rates across intra-subnet and inter-VLAN routes.

2. **Interactive Localhost Web Visualizer (`visualizer/`)**:
   * High-end editorial UI featuring deep obsidian atmosphere, diffused aurora horizon glow, and floating 3D glass spheres.
   * Interactive topology canvas animating packet flows, PDU header decapsulation, and Layer 2 $\leftrightarrow$ Layer 3 transitions.
   * **Fun Element:** Plays Amitabh Bachchan's iconic *"7 Crore!"* (सात करोड़!) meme sound effect with golden confetti upon round-trip packet delivery.

3. **Central IP-MAC Management Database (`network_manager.py`)**:
   * SQLite-backed registry tracking IP-to-MAC bindings, lease timers, and conflict detection.

4. **Viva Defense CLI (`explain.py`)**:
   * Interactive presentation script structuring the defense around **What We Do**, **Why We Do**, and **How We Do**, with a top viva Q&A cheat sheet.

---

## 🛠️ Quickstart & Execution

### 1. Launch the Web Visualizer
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in any modern web browser.

### 2. Run the Cisco Packet Tracer Simulation
Open `IP_MAC_Address_Management_ARP_DHCP.pkt` directly in **Cisco Packet Tracer**. Test pings between:
* `PC1` $\leftrightarrow$ `PC2` (Intra-Subnet ARP)
* `PC1` $\leftrightarrow$ `Core-Gateway` (Default Gateway)
* `PC1` $\leftrightarrow$ `PC5` (Inter-VLAN Routed Traffic across VLAN 10 and 20)

### 3. Run the Viva Defense Explainer
```bash
python explain.py
# Or print the entire script at once:
python explain.py --all
```

---

## 📂 Project Repository Structure

```
CNProject/
├── IP_MAC_Address_Management_ARP_DHCP.pkt   # Native Cisco Packet Tracer simulation
├── IP_MAC_Address_Management_ARP_DHCP.xml   # Decompiled XML project definition
├── generate_pkt.py                          # Automated PKT compilation engine
├── server.py                                # Localhost HTTP & API server
├── network_manager.py                       # SQLite IP-MAC database engine
├── explain.py                               # Interactive Viva defense script
├── app.py                                   # Streamlit management dashboard
├── PROJECT_REPORT.md                        # Academic mini-project report
├── PACKET_TRACER_GUIDE.md                   # Packet Tracer setup & CLI guide
├── visualizer/
│   ├── index.html                           # Interactive Web Visualizer application
│   └── audio/
│       └── 7_crore.mp3                      # 7 Crore celebratory sound effect
└── .gitignore
```
