#!/usr/bin/env python3
"""
explain.py
=================================================================================
Project: IP-MAC Address Management and ARP/DHCP Network Simulation System
Course:  Computer Networks (702AI0C007) - MPSTME / NMIMS
Faculty: Prof. Asha Rawat
Team:    Group 12 (Ananya, Krishna, Siddhant)
=================================================================================
Interactive Presentation & Viva Defense Script:
  - WHAT WE DO  (Project Overview & Core Scope)
  - WHY WE DO   (Problem Statement, Motivation, Network Principles)
  - HOW WE DO   (Topology, Cisco IOS, DORA/ARP Mechanics, Web Visualizer)
=================================================================================
Run with: python explain.py
"""

import sys
import os

# Fix UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ANSI Colors
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"

DIVIDER = f"{CYAN}{'='*80}{RESET}"
SUB_DIV = f"{DIM}{'-'*80}{RESET}"


def print_header():
    print(DIVIDER)
    print(f"{BOLD}{GREEN}  IP-MAC ADDRESS MANAGEMENT & ARP/DHCP NETWORK SIMULATION SYSTEM{RESET}")
    print(f"{CYAN}  Course: Computer Networks (702AI0C007) | MPSTME, NMIMS | Group 12{RESET}")
    print(f"{YELLOW}  Team: Ananya, Krishna, Siddhant | Evaluator: Prof. Asha Rawat{RESET}")
    print(DIVIDER)


def what_we_do():
    print(f"\n{BOLD}{CYAN}[ 1. WHAT WE DO (Project Scope & Deliverables) ]{RESET}\n")
    print(f"{BOLD}In plain words:{RESET}")
    print("  We built a complete, production-grade network simulation and address")
    print("  management system that models, tracks, and visually animates how devices")
    print("  discover each other, acquire IP addresses, and communicate across subnets.")
    print("")
    print(f"{BOLD}Specific Deliverables:{RESET}")
    print(f"  {GREEN}1. Native Cisco Packet Tracer Enterprise Network (.pkt){RESET}")
    print("     - Multi-VLAN architecture (VLAN 10: Dept-A Users, VLAN 20: Dept-B Remote).")
    print("     - Layer 3 Core-Gateway (Catalyst 3650) acting as Inter-VLAN Router and DHCP Server.")
    print("     - Layer 2 Access-Switch (Catalyst 3650) with 802.1Q dot1q trunking and PortFast.")
    print("     - 5 Workstations showcasing Dynamic DHCP, Static Admin, and RARP Reservations.")
    print("")
    print(f"  {GREEN}2. Live Web Visualizer (Runs on http://localhost:8000){RESET}")
    print("     - Interactive canvas showing packet-by-packet data flow across cables.")
    print("     - Full protocol simulation: DHCP DORA handshake, ARP broadcast/unicast,")
    print("       and Cross-VLAN ICMP echo request/reply routing.")
    print("     - Allows Prof. Asha Rawat to select ANY source and ANY destination device")
    print("       and watch real-time PDU frame decapsulation, ARP cache updates, and timers.")
    print("")
    print(f"  {GREEN}3. Python SQLite IP-MAC Database Management Engine{RESET}")
    print("     - Real-time IP-MAC mapping table tracking device identity, lease expiration,")
    print("       and preventing IP collisions/duplicate MAC address spoofing.")
    print(SUB_DIV)


def why_we_do():
    print(f"\n{BOLD}{YELLOW}[ 2. WHY WE DO (The Problem, Motivation & Theory) ]{RESET}\n")
    print(f"{BOLD}The Fundamental Networking Problem:{RESET}")
    print("  Application and Transport layers operate entirely on logical 32-bit IPv4")
    print("  addresses, while physical network cards (NICs) and Ethernet switches ONLY")
    print("  understand 48-bit physical MAC addresses (IEEE 802.3).")
    print("")
    print(f"{BOLD}Why each protocol is indispensable:{RESET}")
    print(f"  {YELLOW}A. Why ARP (Address Resolution Protocol - RFC 826)?{RESET}")
    print("     - Without ARP, a computer knowing an IP address (e.g. 192.168.10.22) has")
    print("       NO WAY to construct an Ethernet frame, because it does not know the")
    print("       hardware MAC address of the destination NIC. ARP bridges Layer 3 to Layer 2.")
    print("")
    print(f"  {YELLOW}B. Why RARP & Modern DHCP Reservations (RFC 903 / RFC 2131)?{RESET}")
    print("     - In diskless workstations or high-security hosts (e.g., PC4 in our project),")
    print("       a machine powers on knowing only its burned-in MAC address (ROM).")
    print("       It needs a mechanism to query the network: 'Here is my MAC, who am I?'")
    print("       While legacy RARP was limited to Layer 2, modern DHCP reservations fulfill")
    print("       this by binding an explicit IP (192.168.10.50) to a client's hardware MAC.")
    print("")
    print(f"  {YELLOW}C. Why Dynamic DHCP (DORA State Machine)?{RESET}")
    print("     - Manual IP configuration in an enterprise with 500+ users causes IP conflicts,")
    print("       subnet mask typos, and gateway misconfigurations. DHCP automates lease")
    print("       allocation, recycling expired addresses dynamically.")
    print("")
    print(f"  {YELLOW}D. Why VLAN Segmentation & Layer 3 Routing?{RESET}")
    print("     - Broadcast containment: An ARP request broadcast (FF:FF:FF:FF:FF:FF) will")
    print("       flood every port in a single subnet, saturating bandwidth. VLANs confine")
    print("       broadcasts within departmental boundaries, while Core-Gateway routes securely.")
    print(SUB_DIV)


def how_we_do():
    print(f"\n{BOLD}{GREEN}[ 3. HOW WE DO (Architecture, Implementation & Execution) ]{RESET}\n")
    print(f"{BOLD}1. Topology Design:{RESET}")
    print("   [Core-Gateway (L3 3650)]  192.168.10.1 (VLAN 10) / 192.168.20.1 (VLAN 20)")
    print("              |")
    print("        [eCrossOver Trunk Link: Gi1/0/1 <--> Gi1/0/24]")
    print("              |")
    print("   [Access-Switch (L2 3650)] PortFast enabled, Rapid-PVST")
    print("      /      |       |       \\       \\")
    print("   PC1      PC2     PC3     PC4      PC5")
    print("  Dynamic  Dynamic  Static  Reserved Remote")
    print("  DHCP     DHCP     Admin   RARP     VLAN 20")
    print("")
    print(f"{BOLD}2. Step-by-Step Packet Mechanics:{RESET}")
    print(f"   {CYAN}A. Step 1 - Dynamic IP Allocation (DHCP DORA):{RESET}")
    print("      1. PC1 broadcasts DHCP DISCOVER (0.0.0.0 -> 255.255.255.255, UDP 67/68).")
    print("      2. Access-Switch carries broadcast over 802.1Q trunk to Core-Gateway.")
    print("      3. Core-Gateway inspects POOL_DEPT_A, reserves 192.168.10.21, sends DHCP OFFER.")
    print("      4. PC1 broadcasts DHCP REQUEST acknowledging the offered configuration.")
    print("      5. Core-Gateway commits lease and responds with unicast DHCP ACK.")
    print("")
    print(f"   {CYAN}B. Step 2 - Intra-Subnet Communication (ARP Resolution):{RESET}")
    print("      1. PC1 wants to ping PC2 (192.168.10.22) on same subnet.")
    print("      2. PC1 checks local ARP cache -> Cache Miss!")
    print("      3. PC1 broadcasts ARP Request: 'Who has 192.168.10.22? Tell 192.168.10.21'.")
    print("      4. Access-Switch floods frame across VLAN 10 ports only.")
    print("      5. PC2 recognizes its own IP, caches PC1's MAC, and sends unicast ARP Reply.")
    print("      6. PC1 updates its ARP cache and sends ICMP Echo Request directly.")
    print("")
    print(f"   {CYAN}C. Step 3 - Inter-Subnet Cross-VLAN Routing (Default Gateway ARP):{RESET}")
    print("      1. PC1 wants to ping PC5 (192.168.20.21 in VLAN 20).")
    print("      2. PC1 inspects subnet mask -> Destination is REMOTE!")
    print("      3. PC1 does NOT ARP for PC5; instead, it ARPs for Default Gateway 192.168.10.1.")
    print("      4. Core-Gateway replies with Vlan10 MAC.")
    print("      5. Frame reaches Core-Gateway -> Decapsulated to Layer 3 IP.")
    print("      6. Core-Gateway routing table routes packet from Vlan10 to Vlan20.")
    print("      7. Core-Gateway encapsulates frame with PC5's MAC and delivers to PC5.")
    print("")
    print(f"{BOLD}3. Web Visualizer & Localhost Engine:{RESET}")
    print("   - Built with HTML5 Canvas, SVG, CSS, and Vanilla JavaScript.")
    print("   - Backed by Python server (server.py) communicating with SQLite database.")
    print("   - Real-time packet animation demonstrates the PDU header changes at each hop.")
    print(SUB_DIV)


def spoken_script():
    print(f"\n{BOLD}{MAGENTA}[ 4. COMPLETE SPOKEN PRESENTATION SCRIPT (For Evaluation / Viva) ]{RESET}\n")
    print(f"{YELLOW}--- SCENE START: Addressing Prof. Asha Rawat ---{RESET}\n")
    
    print(f"{BOLD}{BLUE}[SPEAKER 1: Ananya - Project Introduction & 'WHAT WE DO']{RESET}")
    print('"Good morning Prof. Asha Rawat. Today our group—Group 12, consisting of Ananya,')
    print('Krishna, and Siddhant—is presenting our Computer Networks project titled:')
    print('\'IP-MAC Address Management and ARP/DHCP Network Simulation System\'.')
    print('')
    print('To answer WHAT we have done:')
    print('We have designed and implemented an integrated dual-layer network system:')
    print('First, an enterprise-grade Cisco Packet Tracer simulation featuring a Layer 3')
    print('Core-Gateway, an Access Switch, and 5 multi-department workstations across VLAN 10 and 20.')
    print('Second, a responsive, interactive Web Visualizer running on localhost that provides')
    print('a real-time, packet-by-packet visual walkthrough of address resolution, DHCP DORA,')
    print('and inter-VLAN routing, backed by an IP-MAC SQLite management database."\n')

    print(f"{BOLD}{BLUE}[SPEAKER 2: Krishna - Theoretical Motivation & 'WHY WE DO']{RESET}")
    print('"Now, moving to the critical question: WHY is this system necessary?')
    print('In any network, applications transmit data using Layer 3 IP addresses, but physical')
    print('Ethernet hardware can ONLY switch frames using Layer 2 48-bit MAC addresses.')
    print('')
    print('Without ARP, data transmission is impossible because an IP packet cannot be encapsulated')
    print('into a physical Ethernet frame without knowing the destination hardware address.')
    print('')
    print('Furthermore, manual IP allocation in modern enterprises leads to IP address collisions,')
    print('administrative overhead, and downtime. We implemented DHCP to automate this via the')
    print('4-step DORA state machine. For special hardware like diskless workstations or secure')
    print('servers, we demonstrated the RARP concept using modern DHCP reservations, binding fixed')
    print('IPs to client hardware identifiers. Finally, we segregated users into VLANs to prevent')
    print('broadcast storms and used Layer 3 Inter-VLAN routing to enforce perimeter security."\n')

    print(f"{BOLD}{BLUE}[SPEAKER 3: Siddhant - Technical Architecture & 'HOW WE DO']{RESET}")
    print('"Finally, HOW did we achieve this?')
    print('In our Cisco Packet Tracer environment:')
    print('1. Core-Gateway is a Catalyst 3650 configured with \'ip routing\', hosting SVIs Vlan10')
    print('   and Vlan20, and running Cisco IOS DHCP pools with excluded default gateway ranges.')
    print('2. We established an 802.1Q dot1q trunk over a crossover link to our Access Switch.')
    print('3. On the Access Switch, we configured Rapid Spanning Tree Protocol and PortFast')
    print('   so that ports transition to forwarding immediately without STP drops.')
    print('4. We created 5 distinct host profiles: PC1 and PC2 demonstrate dynamic DHCP and intra-subnet ARP;')
    print('   PC3 represents a static Admin workstation with a hardcoded ARP security entry on the gateway;')
    print('   PC4 demonstrates RARP static DHCP reservation (192.168.10.50) based on client MAC;')
    print('   and PC5 tests cross-subnet inter-VLAN routed pings from VLAN 20.')
    print('')
    print('On our Web Visualizer at localhost:8000, you can select any source and destination')
    print('and observe the exact packet flow: from ARP broadcast flooding, to unicast response,')
    print('to ICMP echo transmission. All processes have been verified with 100% success rate."\n')
    print(f"{YELLOW}--- SCENE END: Handing over for Faculty Questions ---{RESET}")
    print(SUB_DIV)


def viva_qa():
    print(f"\n{BOLD}{RED}[ 5. TOP VIVA QUESTIONS & INSTANT ANSWERS (Prof. Asha Rawat) ]{RESET}\n")
    qa_list = [
        ("Q1: What is the difference between ARP and RARP?",
         "ARP translates a known Layer 3 IP address to an unknown Layer 2 MAC address.\n"
         "  RARP does the exact reverse: a device knows its physical MAC (from ROM) and requests its logical IP.\n"
         "  In modern networks, RARP is superseded by DHCP Reservations."),
        ("Q2: Why did an ARP Request use broadcast, but ARP Reply use unicast?",
         "An ARP Request is broadcast (FF:FF:FF:FF:FF:FF) because the sender does NOT know who owns the IP\n"
         "  or which port they are on. The reply is unicast because the target learned the sender's MAC from\n"
         "  the request header, so it can reply directly without disturbing other nodes."),
        ("Q3: What are the 4 steps of DHCP?",
         "D-O-R-A: Discover (Client broadcast), Offer (Server unicast/broadcast with IP parameters),\n"
         "  Request (Client broadcast confirming selection), Acknowledge/ACK (Server commits lease)."),
        ("Q4: Why does PC1 ARP for the Default Gateway instead of PC5 when pinging PC5?",
         "PC1 applies its subnet mask (255.255.255.0) to PC5's IP (192.168.20.21) and realizes PC5 is on a\n"
         "  different network (192.168.20.0 vs 192.168.10.0). Layer 2 Ethernet cannot cross router boundaries.\n"
         "  Therefore, PC1 must deliver the frame to its Default Gateway (192.168.10.1) for routing."),
        ("Q5: What is an SVI in Cisco switching?",
         "An SVI (Switched Virtual Interface) is a virtual Layer 3 interface on a switch (e.g. 'interface Vlan10')\n"
         "  that provides an IP address and acts as the default gateway for all devices in that VLAN."),
        ("Q6: What is Gratuitous ARP?",
         "An ARP request sent by a host asking for its OWN IP address. It is used to detect duplicate IP\n"
         "  conflicts on the LAN and to announce updated MAC mappings to switch forwarding tables.")
    ]
    for q, a in qa_list:
        print(f"{BOLD}{CYAN}{q}{RESET}")
        print(f"  {GREEN}-> {a}{RESET}\n")
    print(DIVIDER)


def main():
    print_header()
    while True:
        print(f"\n{BOLD}Select an Option to View / Present:{RESET}")
        print("  [1] WHAT WE DO  (Scope, Deliverables & Purpose)")
        print("  [2] WHY WE DO   (Problem Statement, Networking Theory & Justification)")
        print("  [3] HOW WE DO   (Architecture, Protocols, Implementation & DORA/ARP Flow)")
        print("  [4] FULL SPOKEN PRESENTATION SCRIPT (Spoken by Ananya, Krishna, Siddhant)")
        print("  [5] TOP VIVA Q&A CHEAT SHEET (Questions Prof. Asha Rawat may ask)")
        print("  [6] PRINT ENTIRE SCRIPT (All sections in sequence)")
        print("  [0] Exit")
        choice = input(f"\n{BOLD}Enter Choice [0-6]: {RESET}").strip()

        if choice == '1':
            what_we_do()
        elif choice == '2':
            why_we_do()
        elif choice == '3':
            how_we_do()
        elif choice == '4':
            spoken_script()
        elif choice == '5':
            viva_qa()
        elif choice == '6':
            what_we_do()
            why_we_do()
            how_we_do()
            spoken_script()
            viva_qa()
        elif choice == '0':
            print(f"\n{GREEN}Good luck with your viva with Prof. Asha Rawat! Exiting...{RESET}\n")
            break
        else:
            print(f"{RED}Invalid option. Please enter 0 to 6.{RESET}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--all", "-a"):
        print_header()
        what_we_do()
        why_we_do()
        how_we_do()
        spoken_script()
        viva_qa()
    else:
        main()
