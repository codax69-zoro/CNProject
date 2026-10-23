# Cisco Packet Tracer Simulation Guide
## IP-MAC Address Management and ARP/DHCP Network Simulation System

**Course:** Computer Networks (702AI0C007)  
**Institution:** Mukesh Patel School of Technology Management & Engineering (MPSTME), NMIMS  
**Faculty Evaluator:** Prof. Asha Rawat  
**Project Group:** Group 12  
**Team Members:** Ananya, Krishna, Siddhant  

---

## 1. Project Overview & Topology

The simulation file **`IP_MAC_Address_Management_ARP_DHCP.pkt`** simulates an enterprise campus network implementing **Layer 2 and Layer 3 address mapping, dynamic DHCP allocation, intra-subnet and inter-subnet ARP resolution, static IP-MAC binding, and the RARP reservation concept**.

### Topology Architecture

```text
                               +----------------------------------------+
                               |              Core-Gateway              |
                               |    (Catalyst 3560 L3 Switch/Router)    |
                               |     VLAN 10 Gateway: 192.168.10.1      |
                               |     VLAN 20 Gateway: 192.168.20.1      |
                               |         Full Cisco IOS DHCP Server     |
                               +-------------------+--------------------+
                                                   |
                                                   | 802.1Q Trunk Link
                                                   | Core-Gateway Gi1/0/1 <--> Access-Switch Gi1/0/24
                                                   | Allowed VLANs: 10, 20
                                                   |
                               +-------------------+--------------------+
                               |             Access-Switch              |
                               |       (Catalyst 3560 L2 Switch)        |
                               +---+-------+-------+--------+-------+---+
                                   |       |       |        |       |
                 FastEthernet0 <-->|Gi1/0/1|Gi1/0/2|Gi1/0/3 |Gi1/0/4|Gi1/0/5
                                   |       |       |        |       |
                               +---+-+ +---+-+ +---+-+  +---+-+ +---+-+
                               | PC1 | | PC2 | | PC3 |  | PC4 | | PC5 |
                               +-----+ +-----+ +-----+  +-----+ +-----+
                               Dynamic Dynamic Static   Reserved Remote
                                Dept-A  Dept-A  Admin     RARP   Dept-B
                                VLAN 10 VLAN 10 VLAN 10  VLAN 10 VLAN 20
```

---

## 2. Device Addressing & Configuration Table

| Device Name | Interface | MAC Address (BIA) | IPv4 Address | Subnet Mask | Default Gateway | Allocation Type | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Core-Gateway** | `Vlan10` | `0001.9600.0010` | `192.168.10.1` | `255.255.255.0` | N/A | Static | Dept-A Default Gateway & DHCP Server |
| **Core-Gateway** | `Vlan20` | `0001.9600.0020` | `192.168.20.1` | `255.255.255.0` | N/A | Static | Dept-B Default Gateway & DHCP Server |
| **Access-Switch** | `Gi1/0/24` | `0001.9600.0030` | N/A (Trunk) | N/A | N/A | Layer 2 Trunk | Access switch carrying VLAN 10 & 20 |
| **PC1_Dynamic_DeptA** | `FastEth0` | `0002.1664.0010` | Dynamic (DHCP) | `255.255.255.0` | `192.168.10.1` | DHCP Pool | Demonstrates DHCP DORA exchange |
| **PC2_Dynamic_DeptA** | `FastEth0` | `0002.1664.0020` | Dynamic (DHCP) | `255.255.255.0` | `192.168.10.1` | DHCP Pool | Demonstrates Intra-subnet ARP resolution |
| **PC3_Static_Admin** | `FastEth0` | `0002.1664.0030` | `192.168.10.15` | `255.255.255.0` | `192.168.10.1` | Static Manual | High-Security Static IP-MAC mapping |
| **PC4_Reserved_RARP** | `FastEth0` | `0002.1664.0040` | `192.168.10.50` | `255.255.255.0` | `192.168.10.1` | DHCP Reservation | Demonstrates RARP / MAC reservation |
| **PC5_Remote_DeptB** | `FastEth0` | `0002.1664.0050` | Dynamic (DHCP) | `255.255.255.0` | `192.168.20.1` | DHCP Pool | Demonstrates Inter-subnet Gateway ARP |

---

## 3. Step-by-Step Simulation Instructions

### Experiment A: Dynamic IP Allocation (DHCP DORA Process)

1. Open **`IP_MAC_Address_Management_ARP_DHCP.pkt`** in Cisco Packet Tracer.
2. In the bottom-left/middle status bar, toggle the **Fast Forward Time (Alt + D)** button 2-3 times to allow Spanning Tree Protocol (STP) ports to turn green.
3. Click on **PC1_Dynamic_DeptA**:
   - Go to the **Desktop** tab ➡️ click **IP Configuration**.
   - Verify that the **DHCP** radio button is selected.
   - Note the dynamically allocated IP address (e.g. `192.168.10.21`), Subnet Mask `255.255.255.0`, Gateway `192.168.10.1`, and DNS `192.168.10.1`.
4. Click on **PC4_Reserved_RARP**:
   - Verify its IP configuration.
   - Notice that although it is set to **DHCP**, it received the exact static reserved IP **`192.168.10.50`**!
   - This proves the modern implementation of the **RARP concept** (assigning a designated IP based on the client's physical MAC address `0002.1664.0040`).

---

### Experiment B: Observing Address Resolution Protocol (ARP) in Simulation Mode

1. Switch Packet Tracer to **Simulation Mode** (Click the clock/stopwatch icon in the bottom-right corner or press `Shift + S`).
2. In the **Simulation Panel**, click **Show None**, then click **Edit Filters**.
3. Under the **IPv4** tab, check **ARP** and **ICMP**. Uncheck all other filters to keep the event list clean.
4. Click on **PC1_Dynamic_DeptA** ➡️ Open **Command Prompt**:
   - First, inspect the initial empty ARP cache:
     ```cmd
     arp -a
     ```
     *(Output: "No ARP Entries Found")*
   - Now, initiate communication to **PC3_Static_Admin**:
     ```cmd
     ping 192.168.10.15
     ```
5. Click the **Play (Capture Forward)** button step-by-step:
   - **Step 1:** Notice two packets queued on PC1: an **ICMP** packet (waiting for MAC) and an **ARP** packet.
   - **Step 2:** The green ARP packet leaves PC1 and reaches **Access-Switch**.
   - **Step 3:** Access-Switch broadcasts the ARP packet to all active ports (PC2, PC3, PC4, and Trunk).
   - **Step 4:** PC2, PC4, and Core-Gateway inspect the packet, see that their IP does not match `192.168.10.15`, and display a red 'X' (drop frame).
   - **Step 5:** **PC3_Static_Admin** matches the target IP, accepts the frame, and generates a **Unicast ARP Reply** addressed directly to PC1's MAC `0002.1664.0010`.
   - **Step 6:** Access-Switch switches the unicast frame directly to PC1 without broadcasting.
   - **Step 7:** PC1 caches PC3's MAC and immediately transmits the ICMP Echo Request!
6. Click on the green envelope at any step to view the **OSI Model Layers** and **Inbound/Outbound PDU Details** (Opcode, Sender MAC, Target MAC, Sender IP, Target IP).

---

### Experiment C: Inter-Subnet ARP Resolution (Gateway ARP)

1. While still in Simulation Mode, open **PC1_Dynamic_DeptA** Command Prompt.
2. Ping the remote host on VLAN 20 (**PC5_Remote_DeptB**):
   ```cmd
   ping 192.168.20.21
   ```
3. Observe which MAC address PC1 resolves:
   - PC1 recognizes that `192.168.20.21` belongs to an external subnet (`192.168.20.0/24`).
   - PC1 broadcasts an ARP Request NOT for `192.168.20.21`, but for its **Default Gateway `192.168.10.1`**!
   - Core-Gateway responds with its VLAN 10 SVI MAC `0001.9600.0010`.
   - PC1 encapsulates the packet in an Ethernet frame with destination MAC `0001.9600.0010`.

---

## 4. Cisco IOS CLI Verification Commands

To substantiate your project during evaluation, run these commands in the device CLI tabs:

### On Core-Gateway (L3 Switch / Router CLI):

```cisco
Core-Gateway# show ip dhcp binding
! Displays all dynamic leases and static hardware reservations
! Shows IP address, Hardware address (MAC), Lease expiration, and Type

Core-Gateway# show ip arp
! Displays the complete Layer 3 to Layer 2 address resolution table
! Notice the static entry for 192.168.10.15 and dynamic entries for other hosts

Core-Gateway# show ip route
! Verifies connected VLAN 10 and VLAN 20 subnets and inter-VLAN routing

Core-Gateway# show ip dhcp pool
! Displays pool utilization, total addresses, leased addresses, and excluded ranges
```

### On Access-Switch (L2 Switch CLI):

```cisco
Access-Switch# show mac address-table
! Displays the Layer 2 switch forwarding database (MAC address <-> Port mapping)

Access-Switch# show interfaces trunk
! Confirms that GigabitEthernet1/0/24 is operating as an 802.1Q trunk carrying VLAN 10 and 20
```

### On PC Command Prompt:

```cmd
PC1> ipconfig /all
! Displays full IP configuration: IP address, Subnet Mask, Default Gateway, DNS, and Physical MAC

PC1> arp -a
! Displays the learned ARP cache entries with IP address, Physical Address, and Type (dynamic/static)
```

---

## 5. Summary of Viva Answers

- **Q: What is the difference between ARP and RARP?**  
  *A:* ARP translates a known logical IP address into an unknown physical MAC address. RARP does the reverse: a diskless host knowing only its hardware MAC address queries a server to obtain its IP address. RARP was deprecated because it operates only at Layer 2 and cannot provide subnet masks, default gateways, or DNS servers; modern networks use DHCP reservations instead.

- **Q: What happens during the DHCP DORA process?**  
  *A:*  
  1. **Discover:** Client broadcasts to `255.255.255.255` seeking a DHCP server.  
  2. **Offer:** DHCP server reserves an available IP and unicasts/broadcasts an offer with subnet mask, gateway, DNS, and lease time.  
  3. **Request:** Client broadcasts accepting the offered IP.  
  4. **Acknowledge (ACK):** Server commits the binding into its database and sends confirmation to the client.

- **Q: Why does a PC ARP for the Default Gateway instead of the destination IP when pinging a remote subnet?**  
  *A:* MAC addresses are strictly hop-to-hop and cannot cross layer 3 router boundaries. To communicate outside its local subnet, the host must encapsulate the IP packet in a Layer 2 frame addressed to the router's interface MAC address (Default Gateway).
