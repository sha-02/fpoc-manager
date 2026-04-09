FortiOS KVM running 7.4.5-interim for bug fixes of 0985244, 1006546, 1018427

# It does not work if we assign static IP@ for bgp-per-overlay to Hub when combined with dynamic BGP on-loopback for shortcuts

# This is why:

ping from WEST-BR1 to WEST-BR2 reaches WEST-DC1

# flow on WEST-DC1

trace_id=1 func=print_pkt_detail line=5942 msg="vd-root:0 received a packet(proto=1, 10.0.1.101:48564->10.0.2.101:2048) tun_id=10.0.0.4 from EDGE_INET1. type=8, code=0, id=48564, seq=1."
trace_id=1 func=init_ip_session_common line=6127 msg="allocate a new session-000001a0"
trace_id=1 func=__vf_ip_route_input_rcu line=1988 msg="find a route: flag=00000000 gw-10.201.1.2 via EDGE_INET1"
trace_id=1 func=__iprope_tree_check line=524 msg="gnum-100004, use int hash, slot=115, len=2"
trace_id=1 func=fw_forward_handler line=997 msg="Allowed by Policy-12:"
trace_id=1 func=ip_session_confirm_final line=3141 msg="npu_state=0x100, hook=4"
trace_id=1 func=ipsecdev_hard_start_xmit line=662 msg="enter IPSec interface EDGE_INET1, tun_id=0.0.0.0"

The packet goes nowhere for IPsec because no tunnel could be found, hence **it stops at tun_id=0.0.0.0** where trying to find the correct tunnel-id.


# routing

WEST-DC1 (Interim)# get router info routing-table details 10.0.2.101

Routing table for VRF=0
Routing entry for 10.0.2.0/24
  Known via "bgp", distance 200, metric 0, best
  Last update 01:05:32 ago
  * vrf 0 10.201.1.2 priority 11 (recursive is directly connected, EDGE_INET1)
  * vrf 0 10.202.1.2 priority 11 (recursive is directly connected, EDGE_INET2)
  * vrf 0 10.203.1.2 priority 11 (recursive is directly connected, EDGE_MPLS)

WEST-DC1 (Interim)# alias bgp_rib
Routing table for VRF=0
.../...
B       10.0.2.0/24 [200/0] via 10.201.1.2 (recursive is directly connected, EDGE_INET1), 01:07:30, [11/0]
                    [200/0] via 10.202.1.2 (recursive is directly connected, EDGE_INET2), 01:07:30, [11/0]
                    [200/0] via 10.203.1.2 (recursive is directly connected, EDGE_MPLS), 01:07:30, [11/0]
../..


The BGP NH for the destination is in per-overlay ranges 10.{201|202|203}.x.x


# Gateway list does not contain any info about 10.201|202|203.x.x

vd: root/0
**name: EDGE_INET1_1**
version: 2
interface: Internet_1 22
addr: 100.64.11.1:500 -> 100.64.41.10:500
**tun_id: 10.0.0.6**/::10.0.0.8
remote_location: 10.200.1.2
network-id: 11
transport: UDP
virtual-interface-addr: 10.201.1.254 -> **10.200.1.2** **this is the loopback IP received from BR2 via exchange-interface-ip**
created: 4376s ago
**peer-id: WEST-BR2_INET1**
peer-id-auth: no
peer-SN: FGVM04TM20008625
auto-discovery: 1 sender
pending-queue: 0
PPK: no
IKE SA: created 1/1  established 1/1  time 40/40/40 ms
IPsec SA: created 1/1  established 1/1  time 0/0/0 ms

  id/spi: 10 30811cab66a4a544/d9ba1a0678e6da2e
  direction: responder
  status: established 4376-4376s ago = 40ms
  proposal: aes128gcm
  child: no
  SK_ei: de13c99a2c0caa36-75edbda23d2a1298-a3a3ca52
  SK_er: cc7037cfe36ea1cf-0346d2864a1e5c8f-9c6adb5a
  SK_ai:
  SK_ar:
  PPK: no
  message-id sent/recv: 1/3
  QKD: no
  lifetime/rekey: 86400/81753
  DPD sent/recv: 00000000/00000000
  peer-id: WEST-BR2_INET1


# tunnel list

But, because of on-loopback dynBGP for shortcuts, exchange-interface-ip is used to exchange the loopbacks (10.200.x.x) needed for BGP peerings over shortcuts.


WEST-DC1 (Interim)# diagnose vpn tunnel dialup-list EDGE_INET1
list all instance of tunnel EDGE_INET1 in vd 0
------------------------------------------------------
../..
name=**EDGE_INET1_1** ver=2 serial=b 100.64.11.1:0->100.64.41.10:0 nexthop=100.64.11.254 **tun_id=10.0.0.6** tun_id6=::10.0.0.8 status=up dst_mtu=1500 weight=1
bound_if=22 real_if=22 lgwy=static/1 tun=intf mode=dial_inst/3 encap=none/74408 options[122a8]=npu rgwy-chg frag-rfc  run_state=0 role=primary accept_traffic=1 overlay_id=11

parent=EDGE_INET1 index=1
proxyid_num=1 child_num=0 refcnt=5 ilast=0 olast=0 ad=s/1
stat: rxp=10426 txp=10425 rxb=440141 txb=440106
dpd: mode=on-idle on=1 status=ok idle=5000ms retry=2 count=0 seqno=1
natt: mode=none draft=0 interval=0 remote_port=0
fec: egress=0 ingress=0
proxyid=EDGE_INET1 proto=0 sa=1 ref=4 serial=1 ads
  src: 0:0.0.0.0-255.255.255.255:0
  dst: 0:0.0.0.0-255.255.255.255:0
  SA:  ref=3 options=20a02 type=00 soft=0 mtu=1446 expire=38500/0B replaywin=2048
       seqno=28ba esn=0 replaywin_lastseq=000028bb qat=0 rekey=0 hash_search_len=1
  life: type=01 bytes=0/0 timeout=43185/43200
  dec: spi=bbc89cd4 esp=aes-gcm key=20 6727e9d6a546e5d25f802c15f5eeca75b407f88f
       ah=null key=0
  enc: spi=77d0a45e esp=aes-gcm key=20 3e42044353b5c81c32cfa835dcd9e0b8690c90e4
       ah=null key=0
  dec:pkts/bytes=10426/440141, enc:pkts/bytes=10425/1024436
  npu_flag=00 npu_rgwy=100.64.41.10 npu_lgwy=100.64.11.1 npu_selid=7 dec_npuid=0 enc_npuid=0




THere is no way for IPsec to know in which tunnel to send the traffic.


# ##################################################################################################

# Now if I switch to mode-cfg for the tunnels and same setup (per-overlay BGP to Hub, on-loopback dynBGP for shortcuts), it works


Packet is sent to the right tunnel EDGE_INET1_1 based on the tun_id=10.201.1.2 which is the BGP NH of the destination network.

trace_id=1 func=print_pkt_detail line=5942 msg="vd-root:0 received a packet(proto=1, 10.0.1.101:59598->10.0.2.101:2048) tun_id=10.201.1.1 from EDGE_INET1. type=8, code=0, id=59598, seq=1."
trace_id=1 func=init_ip_session_common line=6127 msg="allocate a new session-0000006a"
trace_id=1 func=__vf_ip_route_input_rcu line=1988 msg="find a route: flag=00000000 gw-10.201.1.2 via EDGE_INET1"
trace_id=1 func=__iprope_tree_check line=524 msg="gnum-100004, use int hash, slot=115, len=2"
trace_id=1 func=fw_forward_handler line=997 msg="Allowed by Policy-12:"
trace_id=1 func=ip_session_confirm_final line=3141 msg="npu_state=0x100, hook=4"
trace_id=1 func=ipsecdev_hard_start_xmit line=662 msg="enter IPSec interface EDGE_INET1, tun_id=0.0.0.0"
trace_id=1 func=_do_ipsecdev_hard_start_xmit line=222 **msg="output to IPSec tunnel EDGE_INET1_1, tun_id=10.201.1.2, vrf 0"**
trace_id=1 func=esp_output4 line=917 msg="IPsec encrypt/auth"
trace_id=1 func=nipsec_set_ipsec_sa_enc line=945 msg="Trying to offload IPsec encrypt SA (p1/p2/spi={EDGE_INET1_1/EDGE_INET1/0x6d2cedda}), npudev=-1, skb-dev=Internet_1"
trace_id=1 func=nipsec_set_ipsec_sa_enc line=994 msg="IPSec encrypt SA (p1/p2/spi={EDGE_INET1_1/EDGE_INET1/0x6d2cedda}) offloading-check failed, reason_code=2."
trace_id=1 func=ipsec_output_finish line=676 msg="send to 100.64.11.254 via intf-Internet_1"


WEST-DC1 (Interim)# get router info routing-table details 10.0.2.101

Routing table for VRF=0
Routing entry for 10.0.2.0/24
  Known via "bgp", distance 200, metric 0, best
  Last update 00:00:08 ago
  * vrf 0 10.201.1.2 priority 11 (recursive is directly connected, EDGE_INET1)
  * vrf 0 10.202.1.2 priority 11 (recursive is directly connected, EDGE_INET2)
  * vrf 0 10.203.1.2 priority 11 (recursive is directly connected, EDGE_MPLS)


WEST-DC1 (Interim)# alias rib
../..
B       10.0.2.0/24 [200/0] via 10.201.1.2 (recursive is directly connected, EDGE_INET1), 00:00:10, [11/0]
                    [200/0] via 10.202.1.2 (recursive is directly connected, EDGE_INET2), 00:00:10, [11/0]
                    [200/0] via 10.203.1.2 (recursive is directly connected, EDGE_MPLS), 00:00:10, [11/0]
../..


WEST-DC1 (Interim)# diagnose vpn ike gateway list
../..

vd: root/0
name: EDGE_INET1_1
version: 2
interface: Internet_1 22
addr: 100.64.11.1:500 -> 100.64.41.10:500
tun_id: 10.201.1.2/::10.0.0.8
remote_location: 10.200.1.2
network-id: 11
transport: UDP
virtual-interface-addr: 10.201.1.254 -> **10.200.1.2** **this is the loopback IP received from BR2 via exchange-interface-ip**
created: 80s ago
**peer-id: WEST-BR2_INET1**
peer-id-auth: no
peer-SN: FGVM04TM20008625
**assigned IPv4 address: 10.201.1.2/255.255.255.0** **but the Hub knows BR2 overlay IP because Hub offered during mode-cfg**
auto-discovery: 1 sender
pending-queue: 0
PPK: no
IKE SA: created 1/1  established 1/1  time 40/40/40 ms
IPsec SA: created 1/1  established 1/1  time 0/0/0 ms

  id/spi: 10 b6e000dcb493c22e/8c4ad1c8bf29292a
  direction: responder
  status: established 80-80s ago = 40ms
  proposal: aes128gcm
  child: no
  SK_ei: 9f7e5c2ce604f9e9-35c8d881d4156afd-2069776a
  SK_er: 4bdd85e9510f6b30-2293e3f91d5a9336-9ee9893d
  SK_ai:
  SK_ar:
  PPK: no
  message-id sent/recv: 1/3
  QKD: no
  lifetime/rekey: 86400/86049
  DPD sent/recv: 00000000/00000000
  peer-id: WEST-BR2_INET1


WEST-DC1 (Interim)# diagnose vpn tunnel dialup-list EDGE_INET1
list all instance of tunnel EDGE_INET1 in vd 0
../..
------------------------------------------------------
name=EDGE_INET1_1 ver=2 serial=b 100.64.11.1:0->100.64.41.10:0 nexthop=100.64.11.254 **tun_id=10.201.1.2** tun_id6=::10.0.0.8 status=up dst_mtu=1500 weight=1
bound_if=22 real_if=22 lgwy=static/1 tun=intf mode=dial_inst/3 encap=none/74408 options[122a8]=npu rgwy-chg frag-rfc  run_state=0 role=primary accept_traffic=1 overlay_id=11

parent=EDGE_INET1 index=1
proxyid_num=1 child_num=0 refcnt=5 ilast=0 olast=0 ad=s/1
stat: rxp=175 txp=174 rxb=7686 txb=7632
dpd: mode=on-idle on=1 status=ok idle=5000ms retry=2 count=0 seqno=1
natt: mode=none draft=0 interval=0 remote_port=0
fec: egress=0 ingress=0
proxyid=EDGE_INET1 proto=0 sa=1 ref=4 serial=1 ads
  src: 0:0.0.0.0-255.255.255.255:0
  dst: 0:0.0.0.0-255.255.255.255:0
  SA:  ref=3 options=20a02 type=00 soft=0 mtu=1446 expire=43116/0B replaywin=2048
       seqno=af esn=0 replaywin_lastseq=000000b0 qat=0 rekey=0 hash_search_len=1
  life: type=01 bytes=0/0 timeout=43191/43200
  dec: spi=b578b1a4 esp=aes-gcm key=20 500d630e22ff84ec28995028537b7133e076427b
       ah=null key=0
  enc: spi=6d2cedda esp=aes-gcm key=20 85c323807a9735f2130e72977e2f6ae09a59a467
       ah=null key=0
  dec:pkts/bytes=175/7686, enc:pkts/bytes=174/17384
  npu_flag=00 npu_rgwy=100.64.41.10 npu_lgwy=100.64.11.1 npu_selid=7 dec_npuid=0 enc_npuid=0

