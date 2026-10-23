#!/usr/bin/env python3
"""
app.py
=================================================================================
Web Dashboard: IP-MAC Address Management & ARP/DHCP Network Simulation System
Course:  Computer Networks (702AI0C007) - MPSTME / NMIMS
Faculty: Prof. Asha Rawat
Team:    Ananya, Krishna, Siddhant (Group 12)
=================================================================================
Run with: streamlit run app.py
=================================================================================
"""

import os
import json
import pandas as pd
import streamlit as st
from network_manager import IPMACDatabase, ARPSimulator, RARPSimulator, DHCPSimulator, normalize_mac, format_cisco_mac

st.set_page_config(
    page_title="IP-MAC Management & ARP/DHCP Simulator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0d3b66, #001e3d);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #007bff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .packet-box {
        background: #1e1e1e;
        color: #d4d4d4;
        font-family: monospace;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .badge-static { background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
    .badge-dynamic { background-color: #007bff; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
    .badge-reserved { background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Database & Engines
if "db" not in st.session_state:
    st.session_state.db = IPMACDatabase()
    st.session_state.arp = ARPSimulator(st.session_state.db)
    st.session_state.rarp = RARPSimulator(st.session_state.db)
    st.session_state.dhcp = DHCPSimulator(st.session_state.db)

db = st.session_state.db
arp = st.session_state.arp
rarp = st.session_state.rarp
dhcp = st.session_state.dhcp

# Sidebar info
with st.sidebar:
    st.image("https://img.icons8.com/color/96/server.png", width=70)
    st.title("Project Details")
    st.markdown("**Subject:** Computer Networks (702AI0C007)")
    st.markdown("**Faculty:** Prof. Asha Rawat")
    st.markdown("**Institution:** MPSTME / NMIMS")
    st.markdown("**Group 12 Team Members:**")
    st.markdown("- 👩‍💻 **Ananya**\n- 👨‍💻 **Krishna**\n- 👨‍💻 **Siddhant**")
    st.divider()
    st.markdown("**Core Protocols Simulated:**")
    st.caption("• ARP (Address Resolution Protocol - RFC 826)")
    st.caption("• RARP (Reverse ARP - RFC 903)")
    st.caption("• DHCP (Dynamic Host Config - RFC 2131)")
    st.caption("• IEEE 802.3 MAC Addressing & IP Subnets")
    st.divider()
    st.download_button(
        label="📥 Download Cisco Packet Tracer (.pkt)",
        data=open("IP_MAC_Address_Management_ARP_DHCP.pkt", "rb").read() if os.path.exists("IP_MAC_Address_Management_ARP_DHCP.pkt") else b"",
        file_name="IP_MAC_Address_Management_ARP_DHCP.pkt",
        mime="application/octet-stream"
    )

# Header Banner
st.markdown("""
<div class="main-header">
    <h2 style='margin:0; color: #f4d06f;'>🌐 IP-MAC Address Management & ARP/DHCP Network Simulation System</h2>
    <p style='margin:5px 0 0 0; font-size:16px; opacity:0.9;'>
        Automated IP-MAC database, dynamic DHCP allocation, ARP workflow resolution, and Cisco Packet Tracer integration.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_dash, tab_db, tab_arp, tab_rarp, tab_dhcp, tab_pkt, tab_vis = st.tabs([
    "📊 Dashboard",
    "🗄️ IP-MAC Database",
    "⚡ ARP Workflow Simulator",
    "🔄 RARP & Static Reservations",
    "📡 DHCP DORA Simulator",
    "🛠️ Packet Tracer Lab Guide",
    "✨ 60FPS Packet Visualizer"
])

# ==============================================================================
# TAB 1: DASHBOARD
# ==============================================================================
with tab_dash:
    records = db.get_all()
    total_hosts = len(records)
    static_count = sum(1 for r in records if r['allocation_type'] == 'STATIC')
    dynamic_count = sum(1 for r in records if r['allocation_type'] == 'DYNAMIC_DHCP')
    reserved_count = sum(1 for r in records if r['allocation_type'] == 'RESERVED_RARP')
    vlan10_count = sum(1 for r in records if r['vlan_id'] == 10)
    vlan20_count = sum(1 for r in records if r['vlan_id'] == 20)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total IP-MAC Entries", total_hosts, "Active Hosts")
    with c2:
        st.metric("Static Bindings", static_count, "Gateways & Admin")
    with c3:
        st.metric("Dynamic DHCP Leases", dynamic_count, "Pool Allocations")
    with c4:
        st.metric("RARP / Reserved", reserved_count, "Fixed Hardware MAC")

    st.subheader("Network Topology Summary")
    t1, t2 = st.columns(2)
    with t1:
        st.info("""
        **Subnet 1: VLAN 10 (Dept-A Users & Admin)**
        - **CIDR:** `192.168.10.0/24` (Gateway: `192.168.10.1`)
        - **DHCP Dynamic Pool:** `192.168.10.21` - `192.168.10.254`
        - **Excluded / Static Range:** `192.168.10.1` - `192.168.10.20`
        - **Static Reservation (PC4):** `192.168.10.50` (MAC `00:02:16:64:00:40`)
        """)
    with t2:
        st.info("""
        **Subnet 2: VLAN 20 (Dept-B Remote Pod)**
        - **CIDR:** `192.168.20.0/24` (Gateway: `192.168.20.1`)
        - **DHCP Dynamic Pool:** `192.168.20.21` - `192.168.20.254`
        - **Excluded / Static Range:** `192.168.20.1` - `192.168.20.20`
        - **Gateway ARP Routing:** Inter-subnet communication routed via Core-Gateway
        """)

    st.subheader("Recent System Audit Logs")
    logs = db.get_audit_logs(limit=8)
    if logs:
        st.dataframe(pd.DataFrame(logs)[['timestamp', 'event_type', 'details']], use_container_width=True)

# ==============================================================================
# TAB 2: IP-MAC DATABASE
# ==============================================================================
with tab_db:
    st.subheader("Centralized IP-to-MAC Mapping Database")
    records = db.get_all()
    df = pd.DataFrame(records)

    col_filter, col_export = st.columns([3, 1])
    with col_filter:
        search_query = st.text_input("🔍 Search by Hostname, IP, or MAC Address:", "")
    with col_export:
        st.write("")
        st.download_button(
            "📥 Export to CSV",
            df.to_csv(index=False),
            file_name="ip_mac_database.csv",
            mime="text/csv",
            use_container_width=True
        )

    if search_query:
        mask = df.apply(lambda row: search_query.lower() in str(row).lower(), axis=1)
        df_display = df[mask]
    else:
        df_display = df

    st.dataframe(df_display, use_container_width=True)

    st.divider()
    with st.expander("➕ Add / Update IP-MAC Mapping"):
        with st.form("add_mapping_form"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                f_ip = st.text_input("IP Address (e.g. 192.168.10.75)", "")
                f_mac = st.text_input("MAC Address (e.g. 00:02:16:64:00:75)", "")
            with col_b:
                f_host = st.text_input("Hostname", "Workstation-New")
                f_vlan = st.selectbox("VLAN", [10, 20])
            with col_c:
                f_type = st.selectbox("Allocation Type", ["STATIC", "DYNAMIC_DHCP", "RESERVED_RARP"])
                f_lease = st.number_input("Lease Duration (Seconds)", value=604800, min_value=0)

            submitted = st.form_submit_button("Save Mapping")
            if submitted:
                try:
                    res = db.add_or_update_mapping(
                        ip=f_ip,
                        mac=f_mac,
                        hostname=f_host,
                        subnet=f"192.168.{f_vlan}.0/24",
                        vlan_id=f_vlan,
                        allocation_type=f_type,
                        lease_sec=f_lease
                    )
                    st.success(f"Mapping saved successfully: {res['ip']} -> {res['mac']} ({res['hostname']})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with st.expander("🗑️ Delete IP-MAC Mapping"):
        with st.form("delete_form"):
            del_ip = st.selectbox("Select IP Address to Delete:", [r['ip_address'] for r in records if not r['hostname'].startswith('Core-Gateway')])
            del_submitted = st.form_submit_button("Delete Mapping")
            if del_submitted:
                if db.delete_mapping(del_ip):
                    st.success(f"Deleted IP {del_ip}")
                    st.rerun()

# ==============================================================================
# TAB 3: ARP WORKFLOW SIMULATOR
# ==============================================================================
with tab_arp:
    st.subheader("⚡ Address Resolution Protocol (ARP) Interactive Simulator")
    st.write("Demonstrates how a host resolves a known **Layer 3 IPv4 address** into an unknown **Layer 2 MAC address**.")

    records = db.get_all()
    host_list = [r['hostname'] for r in records if not r['hostname'].startswith('Core-Gateway')]

    c_src, c_dst = st.columns(2)
    with c_src:
        src_host = st.selectbox("Select Source Host:", host_list, index=0)
    with c_dst:
        target_ip = st.selectbox("Select Target IP to Resolve:", [r['ip_address'] for r in records if r['hostname'] != src_host])

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        run_arp = st.button("🚀 Execute ARP Resolution", type="primary", use_container_width=True)
    with col_btn2:
        clear_arp_cache = st.button("🧹 Flush Local ARP Cache", use_container_width=True)

    if clear_arp_cache:
        arp.clear_cache(src_host)
        st.toast(f"ARP Cache cleared for {src_host}")

    if run_arp:
        result = arp.simulate_resolution(src_host, target_ip)
        st.subheader("Simulation Results")

        if result['cache_hit']:
            st.success(f"🎯 **CACHE HIT!** IP `{target_ip}` was already cached with MAC `{result['mac']}`. No broadcast packet sent!")
        else:
            st.info(f"🔍 **CACHE MISS!** ARP broadcast packet sent and replied.")

        # Step by Step timeline
        for t in result['trace']:
            with st.container():
                st.markdown(f"**Step {t['step']}: {t['title']}**")
                st.write(t['details'])
                if t.get('packet'):
                    st.json(t['packet'])
                st.divider()

    st.subheader("🛡️ Gratuitous ARP (Duplicate IP Detection)")
    with st.expander("Test Gratuitous ARP for an Active Host"):
        g_host = st.selectbox("Select Host for Gratuitous ARP:", host_list, key="grat_host")
        if st.button("Broadcast Gratuitous ARP"):
            g_res = arp.simulate_gratuitous_arp(g_host)
            st.success(f"Gratuitous ARP broadcast for {g_res['ip']} ({g_res['mac']}). Result: {g_res['result']}")
            st.json(g_res['packet'])

# ==============================================================================
# TAB 4: RARP & STATIC RESERVATIONS
# ==============================================================================
with tab_rarp:
    st.subheader("🔄 Reverse Address Resolution Protocol (RARP) & Modern DHCP Reservations")
    st.write("""
    **Theoretical Concept:** 
    * **ARP:** Knows Target IP ➡️ Resolves Unknown MAC.
    * **RARP:** Knows Own MAC (from ROM/NIC) ➡️ Queries Server for Assigned IP.
    * **Historical Context:** RARP was used by diskless workstations at boot time. It operates strictly at Layer 2 (EtherType `0x8035`), meaning RARP broadcasts cannot cross routers and cannot provide subnet masks or gateways.
    * **Modern Replacement:** Modern enterprise networks implement the RARP concept via **DHCP Static Reservations** (binding fixed IP to MAC).
    """)

    st.divider()
    c_rarp_query, c_rarp_res = st.columns(2)
    with c_rarp_query:
        st.markdown("#### Test RARP / Static Reservation Query")
        query_mac = st.text_input("Enter Hardware MAC Address to Resolve:", "00:02:16:64:00:40")
        if st.button("Query RARP Server"):
            res = rarp.query_rarp(query_mac)
            if res['success']:
                st.success(f"✅ RARP Success: Hardware MAC `{res['mac']}` is assigned IP **`{res['assigned_ip']}`** ({res['hostname']})")
                st.info(res['explanation'])
                st.markdown("**Decoded RARP Reply Packet:**")
                st.json(res['reply_packet'])
            else:
                st.error(f"❌ RARP Failed: {res['explanation']}")
                st.json(res['request_packet'])

    with c_rarp_res:
        st.markdown("#### Comparison Matrix: ARP vs. RARP vs. DHCP")
        comp_df = pd.DataFrame([
            {"Protocol": "ARP", "Layer": "Network/Link (2/3)", "Known": "IP Address", "Discovered": "MAC Address", "Scope": "Local Broadcast", "Status": "Active Standard"},
            {"Protocol": "RARP", "Layer": "Data Link (2)", "Known": "MAC Address", "Discovered": "IP Address Only", "Scope": "Local Broadcast Only", "Status": "Deprecated (Obsolete)"},
            {"Protocol": "DHCP", "Layer": "Application (UDP 67/68)", "Known": "MAC Address", "Discovered": "IP, Mask, GW, DNS, Lease", "Scope": "Routable (DHCP Relay)", "Status": "Modern Enterprise Standard"},
        ])
        st.table(comp_df)

# ==============================================================================
# TAB 5: DHCP DORA SIMULATOR
# ==============================================================================
with tab_dhcp:
    st.subheader("📡 Dynamic Host Configuration Protocol (DHCP) DORA Simulator")
    st.write("Demonstrates the 4-way **D-O-R-A** handshake for automatic and dynamic IP address assignment.")

    with st.form("dhcp_form"):
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            dhcp_hostname = st.text_input("New Client Hostname:", "Laptop-Finance")
        with col_d2:
            dhcp_mac = st.text_input("Client Physical MAC Address:", "00:02:16:64:00:88")
        with col_d3:
            dhcp_vlan = st.selectbox("Destination VLAN / Department:", [10, 20])
        sim_dhcp = st.form_submit_button("⚡ Simulate DHCP DORA Exchange", type="primary")

    if sim_dhcp:
        try:
            d_res = dhcp.simulate_dora(dhcp_hostname, dhcp_mac, vlan_id=dhcp_vlan)
            st.success(f"🎉 IP Allocation Successful! Assigned **{d_res['allocated_ip']}** to `{d_res['hostname']}` (Type: {d_res['allocation_type']})")

            st.markdown("### DORA Protocol Handshake Timeline")
            for step in d_res['steps']:
                with st.expander(f"Step [{step['step']}] - {step['name']}: {step['from']} ➡️ {step['to']}", expanded=True):
                    st.write(step['desc'])
                    st.json(step['packet'])

        except Exception as ex:
            st.error(f"Error during DHCP DORA simulation: {ex}")

# ==============================================================================
# TAB 6: PACKET TRACER LAB GUIDE & IOS EXPORTER
# ==============================================================================
with tab_pkt:
    st.subheader("🛠️ Cisco Packet Tracer Lab Guide & Cisco IOS Commands")
    st.markdown("""
    Your project file **`IP_MAC_Address_Management_ARP_DHCP.pkt`** contains a fully connected, pre-configured enterprise topology:
    - **Core-Gateway (Catalyst 3560 MultiLayer Switch / Router)**: Performs Inter-VLAN routing, Layer 3 Gateway, and DHCP Server for VLAN 10 and VLAN 20.
    - **Access-Switch (Catalyst 3560 Layer 2 Switch)**: Access switch with dot1q trunking and client access ports.
    - **End Devices**: Dynamic DHCP Clients, Static High-Security Admin Host, and Reserved RARP Host.
    """)

    st.subheader("Topology Diagram")
    st.code("""
                               +----------------------------------------+
                               |              Core-Gateway              |
                               |    (Catalyst 3560 L3 Switch/Router)    |
                               |     VLAN 10 Gateway: 192.168.10.1      |
                               |     VLAN 20 Gateway: 192.168.20.1      |
                               |         Full Cisco IOS DHCP Server     |
                               +-------------------+--------------------+
                                                   |
                                                   | Trunk (Gi1/0/1 to Gi1/0/24)
                                                   | 802.1Q Allowed: 10, 20
                                                   |
                               +-------------------+--------------------+
                               |             Access-Switch              |
                               |        (Catalyst 3560 L2 Access)       |
                               +---+-----------+------------+-------+---+
                                   |           |            |       |
                                   | Gi1/0/1   | Gi1/0/2    | Gi1/0/3  | Gi1/0/4
                                   |           |            |       |
                              +----+--+   +----+--+    +----+---+ +-+----+
                              |  PC1  |   |  PC2  |    |  PC3   | | PC4  |
                              +-------+   +-------+    +--------+ +------+
                              Dynamic      Dynamic       Static    RARP/
                               DHCP         DHCP         Admin    Reserved
                            (Dept-A)     (Dept-A)    192.168.10.15 192.168.10.50
    """, language="text")

    st.subheader("Step-by-Step Lab Simulation Instructions")
    st.markdown("""
    1. **Open the File:** Double-click `IP_MAC_Address_Management_ARP_DHCP.pkt` to launch Cisco Packet Tracer.
    2. **Observe DHCP Allocation (Realtime Mode):**
       - Click on **PC1_Dynamic_DeptA** ➡️ Go to **Desktop** ➡️ **IP Configuration**.
       - Notice that it is set to **DHCP** and receives an IP address automatically from the `192.168.10.0/24` pool!
       - Check **PC4_Reserved_RARP**: Notice it receives **`192.168.10.50`** via static hardware reservation!
    3. **Observe ARP in Simulation Mode:**
       - Switch to **Simulation Mode** (bottom-right icon or `Shift + S`).
       - Click **Show None / Edit Filters** and check only **ARP** and **DHCP**.
       - Open **PC1_Dynamic_DeptA** Command Prompt and type: `ping 192.168.10.15`.
       - Click the **Play / Capture Forward** button.
       - Watch the green ARP envelope broadcast to the switch and reach PC3, and watch PC3 unicast the ARP reply back!
    4. **Inspect Router / Switch CLI:**
       - Click on **Core-Gateway** ➡️ Go to the **CLI** tab:
         ```bash
         Core-Gateway# show ip dhcp binding
         Core-Gateway# show ip arp
         Core-Gateway# show ip route
         ```
       - Click on **Access-Switch** ➡️ Go to the **CLI** tab:
         ```bash
         Access-Switch# show mac address-table
         ```
    """)

    st.subheader("Exported Cisco IOS Configuration Script")
    st.code(db.generate_cisco_ios_commands(), language="cisco")

# ==============================================================================
# TAB 7: 60FPS PACKET TRANSFER VISUALIZER
# ==============================================================================
with tab_vis:
    st.subheader("✨ 60FPS Rich Packet Transfer Visualizer (Localhost)")
    st.markdown("""
    The dedicated UI-rich network packet visualizer runs natively in your browser on `http://localhost:8000`.
    It shows real-time animated packets traveling across cables, switch broadcast flooding, unicast replies, and full OSI PDU inspection.
    """)

    st.info("💡 To launch the visualizer independently, run: `python server.py` in your terminal.")

    st.markdown(
        '<a href="http://localhost:8000" target="_blank" style="text-decoration:none;">'
        '<button style="background:linear-gradient(135deg,#0072ff,#00d2ff); color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:700; cursor:pointer;">'
        '🚀 Open Visualizer in Fullscreen (http://localhost:8000)'
        '</button></a>',
        unsafe_allow_html=True
    )

    st.write("")
    # Embed iframe preview
    st.components.v1.iframe("http://localhost:8000", height=650, scrolling=True)

