#!/usr/bin/env python3
"""Generates Topology-detailed.drawio (multi-page) from the data read off the Visio PDF."""
from xml.sax.saxutils import escape

# ---- palette (link-type colour coding, same on every page) -------------------
C_TRUNK = "#1F4E79"   # 802.1Q trunk over LACP port-channel
C_ISP = "#D79B00"     # ISP hand-off
C_IN = "#2E7D32"      # firewall inside
C_OUT = "#C62828"     # firewall outside
C_HA = "#C62828"      # HA / state-failover
C_MGMT = "#757575"    # management
C_WAN = "#000000"     # inter-site


class Page:
    def __init__(self, name, w=1700, h=1200):
        self.name, self.w, self.h = name, w, h
        self.cells, self.n = [], 1

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def box(self, label, x, y, w, h, style, id=None):
        id = id or self._id()
        self.cells.append(
            f'<mxCell id="{id}" value="{escape(label, {chr(34): "&quot;"})}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return id

    def text(self, label, x, y, w, h, extra=""):
        return self.box(label, x, y, w, h,
                        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=11;" + extra)

    def zone(self, label, x, y, w, h, color="#F5F5F5", stroke="#9E9E9E", dashed=1):
        return self.box(label, x, y, w, h,
                        f"rounded=0;html=1;whiteSpace=wrap;fillColor={color};strokeColor={stroke};"
                        f"dashed={dashed};verticalAlign=top;align=left;spacingLeft=8;fontStyle=1;fontSize=12;"
                        "fontColor=#444444;container=0;")

    # devices -----------------------------------------------------------------
    def dev(self, icon, label, x, y, w=120, h=70, fill="#FAFBFB", stroke="#005073", fc="#000000"):
        return self.box(label, x, y, w, h,
                        f"shape=mxgraph.cisco19.rect;prIcon={icon};html=1;whiteSpace=wrap;verticalLabelPosition=bottom;"
                        f"verticalAlign=top;fillColor={fill};strokeColor={stroke};fontColor={fc};fontSize=11;fontStyle=1;")

    def router(self, l, x, y): return self.dev("router", l, x, y, 90, 70)
    def l3(self, l, x, y, w=260): return self.dev("l3_switch", l, x, y, w, 70, "#D5E8F4", "#005073")
    def l2(self, l, x, y): return self.dev("l2_switch", l, x, y, 100, 50, "#EEEEEE", "#666666")
    def ftd(self, l, x, y): return self.dev("firewall", l, x, y, 100, 70, "#DAE8FC", "#1F4E79")
    def pa(self, l, x, y): return self.dev("firewall", l, x, y, 100, 70, "#F8CECC", "#B85450")

    def cloud(self, label, x, y):
        return self.box(label, x, y, 150, 80,
                        "ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#FFE6A8;strokeColor=#D79B00;fontStyle=1;fontSize=12;fontColor=#C62828;")

    def stack_note(self, x, y, w, txt):
        return self.text(txt, x, y, w, 30, "fontSize=10;fontColor=#555555;align=center;")

    # link --------------------------------------------------------------------
    def link(self, a, b, label="", color=C_TRUNK, src="", dst="", dashed=0, w=2,
             ex=None, en=None, pts=None, curved=0):
        """ex/en = (x,y) fractions on source/target; src/dst = endpoint (port) labels."""
        id = self._id()
        pos = ""
        if ex: pos += f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;"
        if en: pos += f"entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;"
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;startArrow=none;"
                 f"strokeColor={color};strokeWidth={w};dashed={dashed};fontSize=10;fontColor={color};fontStyle=1;{pos}")
        p = ""
        if pts:
            p = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts) + "</Array>"
        self.cells.append(
            f'<mxCell id="{id}" value="{escape(label)}" style="{style}" edge="1" parent="1" source="{a}" target="{b}">'
            f'<mxGeometry relative="1" as="geometry">{p}</mxGeometry></mxCell>')
        for pos_x, txt in ((-0.78, src), (0.78, dst)):
            if txt:
                self.cells.append(
                    f'<mxCell id="{self._id()}" value="{escape(txt)}" style="edgeLabel;html=1;align=center;verticalAlign=middle;'
                    f'fontSize=9;fillColor=#EEF3E2;strokeColor=#B5C09A;spacing=2;" vertex="1" connectable="0" parent="{id}">'
                    f'<mxGeometry x="{pos_x}" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')
        return id

    def title(self, t, sub):
        self.text(f"<b style='font-size:20px'>{t}</b><br/><span style='color:#666666'>{sub}</span>", 20, 10, 1200, 50)

    def legend(self, x, y):
        rows = [(C_TRUNK, 0, "802.1Q trunk / LACP port-channel (PoX)"), (C_ISP, 0, "ISP hand-off (access / trunk)"),
                (C_IN, 0, "Firewall INSIDE"), (C_OUT, 0, "Firewall OUTSIDE"),
                (C_HA, 1, "HA / State-Failover (dashed)"), (C_MGMT, 1, "Management (dashed)"),
                (C_WAN, 0, "Inter-site link (thick)")]
        self.zone("LEGEND", x, y, 300, 30 + 24 * len(rows) + 50, "#FFFFFF", "#666666", 0)
        for i, (c, d, t) in enumerate(rows):
            yy = y + 38 + 24 * i
            self.box("", x + 12, yy + 8, 50, 2, f"rounded=0;fillColor={c};strokeColor={c};dashed={d};")
            self.text(t, x + 72, yy, 220, 20, "fontSize=10;")
        self.text("Endpoint label = <b>PoX</b> + member ports<br/>Centre label = allowed VLANs", x + 12,
                  y + 38 + 24 * len(rows), 280, 40, "fontSize=10;")

    def xml(self, idx):
        return (f'<diagram id="p{idx}" name="{escape(self.name)}"><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" '
                f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.w}" '
                f'pageHeight="{self.h}" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                + "".join(self.cells) + "</root></mxGraphModel></diagram>")


pages = []

# =============================================================================
# 0. OVERVIEW
# =============================================================================
p = Page("0 - Overview (WAN/Sites)", 1700, 1000)
p.title("Network Overview - 3 Sites", "Level-1 view: sites, ISPs, inter-site links. Details on following pages.")
p.zone("SITE A - JIQ Office (Campus)", 20, 80, 520, 760, "#F7FBFF", "#1F4E79")
p.zone("SITE B - DC-1 (FTD ACTIVE 192.168.2.100)", 580, 80, 520, 760, "#F9FFF7", "#2E7D32")
p.zone("SITE C - DC-2 (FTD PASSIVE 172.16.2.248)", 1140, 80, 520, 760, "#FFF9F5", "#B85450")
cA1, cA2 = p.cloud("MAGTI", 60, 130), p.cloud("System Net", 340, 130)
rA1, rA2 = p.router("C8300-R1", 95, 280), p.router("C8300-R2", 375, 280)
coreA = p.l3("C9300 StackWise (Core/Dist)", 190, 440, 240)
fwA = p.pa("PaloAlto FW1/FW2 (A/P HA)", 40, 600)
vpnA = p.ftd("RMT-VPN FTD2110 (A/P)", 220, 600)
accA = p.l2("9x C9200 Access<br/>(9200-2 .. 9200-9)", 400, 600)
cB1, cB2 = p.cloud("TBC BANK", 620, 130), p.cloud("SILK", 900, 130)
rB = p.router("C8300-R1", 755, 280)
coreB = p.l3("C9300 StackWise", 700, 440, 240)
ftdB = p.ftd("FTD2110 ACTIVE", 900, 600)
hpeB = p.l3("HPE 5700 IRF Stack", 620, 700, 200)
cC1, cC2 = p.cloud("MAGTI", 1180, 130), p.cloud("TBC BANK", 1460, 130)
rC = p.router("C8300-R2", 1315, 280)
coreC = p.l3("C9300 StackWise", 1260, 440, 240)
ftdC = p.ftd("FTD2110 PASSIVE", 1460, 600)
hpeC = p.l3("HPE 5700 IRF Stack", 1180, 700, 200)
p.link(cA1, rA1, "V1555", C_ISP, dst="G0/0/4"); p.link(cA2, rA2, "V1555", C_ISP, dst="G0/0/2")
p.link(rA1, coreA, "Po1 -> Po30", ex=(0.5, 1), en=(0.2, 0)); p.link(rA2, coreA, "Po1 -> Po31", ex=(0.5, 1), en=(0.8, 0))
p.link(coreA, fwA, "Po20-23", C_IN, ex=(0.1, 1), en=(0.5, 0)); p.link(coreA, vpnA, "Po25-28", C_OUT, ex=(0.5, 1), en=(0.5, 0))
p.link(coreA, accA, "Po1..", ex=(0.9, 1), en=(0.5, 0))
p.link(cB1, rB, "Access V1505 via ISP SW", C_ISP); p.link(cB2, rB, "Access", C_ISP)
p.link(rB, coreB, "Po1 -> Po4 V92,93,100-103"); p.link(coreB, ftdB, "Po2 Outside", C_OUT, ex=(1, 0.5), en=(0.5, 0))
p.link(coreB, hpeB, "Po1 -> BAGG31 Trunk", ex=(0.2, 1), en=(0.5, 0)); p.link(ftdB, hpeB, "Po3 Inside / Po1 V201 HA", C_IN, ex=(0.5, 1), en=(1, 0.5))
p.link(cC1, rC, "V1555", C_ISP); p.link(cC2, rC, "Access V1505 via ISP SW", C_ISP)
p.link(rC, coreC, "Po1 -> Po4 V91,94,100-103"); p.link(coreC, ftdC, "Po2 Outside", C_OUT, ex=(1, 0.5), en=(0.5, 0))
p.link(coreC, hpeC, "Po1 -> BAGG29 V108-125,300", ex=(0.2, 1), en=(0.5, 0)); p.link(ftdC, hpeC, "Po3 Inside / Po1 V201 HA", C_IN, ex=(0.5, 1), en=(1, 0.5))
p.link(coreA, hpeB, "Te1/1/1 <-> Te1/0/30  ALL VLANS (trunk)", C_WAN, w=4, ex=(1, 0.5), en=(0, 0.5), pts=[(560, 860)], dst="Te1/0/30", src="Te1/1/1")
p.link(hpeB, hpeC, "BAGG36 (4x10G: Te1/0/35,36 + Te2/0/35,36 <-> Te1/0/33,34 + Te2/0/33,34)", C_WAN, w=4, ex=(0.5, 1), en=(0.5, 1), pts=[(720, 900), (1280, 900)])
p.legend(20, 860)
pages.append(p)

# =============================================================================
# 1. SITE A
# =============================================================================
p = Page("1 - Site A JIQ Office L2-L3", 1800, 1500)
p.title("Site A - JIQ Office : L2/L3 Detail",
        "ISP edge -> C8300 routers -> C9300 StackWise core -> Firewalls (PaloAlto + RMT-VPN FTD) -> C9200 access")
rows = [("ISP", 70, 130), ("EDGE ROUTERS", 210, 190), ("CORE / DISTRIBUTION", 430, 230), ("SECURITY", 430, 230), ("ACCESS", 940, 520)]
p.zone("LAYER 1 - ISP", 20, 70, 1760, 130, "#FFFBEA", "#D79B00")
p.zone("LAYER 2 - WAN EDGE (C8300)", 20, 210, 1760, 190, "#F3F0FA", "#6C3FA0")
p.zone("LAYER 3 - CORE / DISTRIBUTION + FIREWALLS (inline, A/P)", 20, 410, 1760, 520, "#F4F9FD", "#1F4E79")
p.zone("LAYER 4 - ACCESS (C9200 per IDF/floor group)", 20, 940, 1760, 520, "#FAFAFA", "#757575")
isp1, isp2 = p.cloud("MAGTI", 300, 90), p.cloud("System Net", 1250, 90)
r1, r2 = p.router("C8300-R1", 345, 250), p.router("C8300-R2", 1295, 250)
core = p.l3("C9300 StackWise<br/>(Gi1/x = member 1, Gi2/x = member 2) Te1/1/1 -> Site B", 760, 560, 280)
fw1, fw2 = p.pa("PaloAlto FW1<br/>ACTIVE", 150, 540), p.pa("PaloAlto FW2<br/>PASSIVE", 1550, 540)
v1, v2 = p.ftd("RMT-VPN FTD2110<br/>ACTIVE (192.168.2.100)", 150, 760), p.ftd("RMT-VPN FTD2110<br/>PASSIVE (192.168.2.101)", 1550, 760)
p.link(isp1, r1, "V1555", C_ISP, dst="G0/0/4"); p.link(isp2, r2, "V1555", C_ISP, dst="G0/0/2")
p.link(r1, core, "V10,126-127,200,202,204,206", src="Po1<br/>Gi0/0/0, Gi0/0/1", dst="Po30<br/>Gi1/0/30, Gi2/0/30", ex=(0.5, 1), en=(0.2, 0))
p.link(r2, core, "V126-127,201-202,205-206", src="Po1<br/>Gi0/0/0, Gi0/0/1", dst="Po31<br/>Gi1/0/31, Gi2/0/31", ex=(0.5, 1), en=(0.8, 0))
p.link(fw1, core, "INSIDE ACTIVE  V106-125,203,300-304", C_IN, src="Po20<br/>Eth1/2, Eth1/4", dst="Gi1/0/20, Gi2/0/21", ex=(1, 0.3), en=(0, 0.3))
p.link(fw1, core, "OUTSIDE ACTIVE  V200,201,204,205", C_OUT, src="Po21<br/>Eth1/3, Eth1/1", dst="Gi1/0/22, Gi2/0/23", ex=(1, 0.7), en=(0, 0.7))
p.link(fw2, core, "INSIDE PASSIVE  V106-125,203,300-304", C_IN, src="Po22<br/>Eth1/2, Eth1/4", dst="Gi1/0/21, Gi2/0/20", ex=(0, 0.3), en=(1, 0.3))
p.link(fw2, core, "OUTSIDE PASSIVE  V200,201,204,205", C_OUT, src="Po23<br/>Eth1/1, Eth1/3", dst="Gi1/0/23, Gi2/0/22", ex=(0, 0.7), en=(1, 0.7))
p.link(fw1, fw2, "HA (Eth1/11, Eth1/12)", C_HA, dashed=1, ex=(0.5, 0), en=(0.5, 0), pts=[(200, 480), (1600, 480)])
p.link(v1, core, "Outside V304", C_OUT, src="Po10<br/>Eth1/1, Eth1/2", dst="Po25<br/>Gi1/0/25, Gi2/0/25", ex=(1, 0.3), en=(0.1, 1))
p.link(v1, core, "Management V304", C_MGMT, dashed=1, src="Po20<br/>Eth1/3, Eth1/4", dst="Po26<br/>Gi1/0/26, Gi2/0/26", ex=(1, 0.7), en=(0.25, 1))
p.link(v2, core, "Outside V304", C_OUT, src="Po10<br/>Eth1/1, Eth1/2", dst="Po27<br/>Gi1/0/27, Gi2/0/27", ex=(0, 0.3), en=(0.9, 1))
p.link(v2, core, "Management V304", C_MGMT, dashed=1, src="Po10<br/>Eth1/3, Eth1/4", dst="Po28<br/>Gi1/0/28, Gi2/0/28", ex=(0, 0.7), en=(0.75, 1))
p.link(v1, v2, "FTD HA/failover (to be confirmed)", C_HA, dashed=1, ex=(0.5, 1), en=(0.5, 1), pts=[(200, 900), (1600, 900)])
# access switches (name, label, x, y, uplink on core, trunk VLANs, local VLANs)
acc = [("JIQ-OFFICE-9200-2#", 120, 1000, "Po1", "V108-125,300", ""),
       ("JIQ-OFFICE-9200-3#", 380, 1000, "Po3", "V108-125,300", "V1,71,164,172,1000"),
       ("JIQ-OFFICE-9200-4#", 1010, 1000, "Po?", "V108-125,300-302", ""),
       ("JIQ-OFFICE-9200-4#*", 1330, 1000, "Po?", "V108-125,300", "V1,31,32,130,164,172,1000"),
       ("JIQ-OFFICE-9200-5#", 120, 1210, "Po2", "V108-125,300", "V1,33,164,172,1000"),
       ("JIQ-OFFICE-9200-6#", 700, 1210, "Po?", "V1,63,1000", ""),
       ("JIQ-OFFICE-9200-7#", 1330, 1210, "Po?", "V108-125,300", ""),
       ("JIQ-OFFICE-9200-8#", 250, 1390, "-", "V108-125,300", ""),
       ("JIQ-OFFICE-9200-9#", 1330, 1390, "-", "V108-125,300", "")]
for i, (n, x, y, po, tv, lv) in enumerate(acc):
    s = p.l2(n + (f"<br/><i style='font-weight:normal'>local: {lv}</i>" if lv else ""), x, y)
    up = "Po1<br/>Gi1/0/23, Gi1/0/24" if n[-3] not in "89" else ""
    p.link(core, s, tv, C_TRUNK, src=po, dst=up, ex=(0.08 + 0.105 * i, 1), en=(0.5, 0))
p.text("<b>Notes (from Visio source - verify):</b><br/>* Source has two switches labelled 9200-4#; 2nd renamed 9200-4#* here.<br/>"
       "Po? = core-side port-channel number not visible in source.<br/>9200-8/9 have no uplink port labels in source.<br/>"
       "Local VLANs assignment per switch inferred from label placement.", 1000, 1380, 520, 90, "fontSize=10;fontColor=#B85450;")
p.legend(1480, 80)
pages.append(p)


# =============================================================================
# 2/3. SITE B and C (same pattern)
# =============================================================================
def dc(name, title, r_name, mem_a, mem_b, isp_l, isp_r, isp_sw_first, vl_r, core_po_r, r_core_ports, hpe_core_po, hpe_core_po_ports,
       hpe_core_vl, ftd_label, ftd_vl_out, ftd_hpe_ports, fail_ports, hpe_bagg36, up_note):
    p = Page(name, 1700, 1450)
    p.title(title, "ISP -> C8300 -> C9300 StackWise -> FTD2110 (A/P) -> HPE 5700 IRF stack (server/DC aggregation)")
    p.zone("LAYER 1 - ISP", 20, 70, 1660, 200, "#FFFBEA", "#D79B00")
    p.zone("LAYER 2 - WAN EDGE", 20, 280, 1660, 190, "#F3F0FA", "#6C3FA0")
    p.zone("LAYER 3 - CORE / DISTRIBUTION", 20, 480, 1660, 200, "#F4F9FD", "#1F4E79")
    p.zone("LAYER 4 - SECURITY + DC AGGREGATION", 20, 690, 1660, 700, "#F7FBF4", "#2E7D32")
    a, b = p.cloud(isp_l, 200, 90), p.cloud(isp_r, 900, 90)
    sw = p.l2("ISP SW<br/>(ISP-owned)", 560, 175)
    r = p.router(r_name, 600, 320)
    core = p.l3("C9300 StackWise", 540, 530, 260)
    ftd = p.ftd(ftd_label, 1000, 760)
    hpe = p.l3("HPE 5700 IRF Stack<br/>(IRF-port 1/1 &lt;-&gt; 2/2 via Te1/0/37-40)", 300, 1100, 300)
    far = p.box("to Site (remote)<br/>" + up_note, 60, 1150, 180, 70,
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontSize=10;")
    far2 = p.box("DC peer site<br/>HPE 5700 stack BAGG36", 1100, 1150, 220, 70,
                 "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontSize=10;")
    p.link(a, sw if isp_sw_first == "L" else r, "Access V1505" if isp_sw_first == "L" else "V1555", C_ISP, dst="G0/11" if isp_sw_first == "L" else "G0/0/4")
    if isp_sw_first == "L":
        p.link(sw, r, "Trunk V1505", C_ISP, src="G0/1", dst="G0/0/3")
        p.link(b, r, "Access", C_ISP, dst="G0/0/4")
    else:
        p.link(b, sw, "Access V1505", C_ISP, dst="G0/11")
        p.link(sw, r, "Trunk V1505", C_ISP, src="G0/1", dst="G0/0/3")
    p.link(r, core, vl_r, src="Po1<br/>Gi0/0/0, Gi0/0/1", dst=f"{core_po_r}<br/>{r_core_ports}", ex=(0.5, 1), en=(0.5, 0))
    p.link(core, ftd, "OUTSIDE  V10,30,70,100,102,103,203", C_OUT, src=ftd_vl_out[0], dst="Po2<br/>Eth1/1, Eth1/2", ex=(1, 0.5), en=(0.5, 0))
    p.link(core, hpe, hpe_core_vl, C_TRUNK, src=f"{hpe_core_po}<br/>{hpe_core_po_ports[0]}", dst=hpe_core_po_ports[1], ex=(0.3, 1), en=(0.5, 0))
    p.link(ftd, hpe, "INSIDE  V10,20,40,50,60,70,80,110,120,140,203,400,500,600,700,800,900,1000,1208", C_IN,
           src="Po3<br/>Eth1/3, Eth1/4", dst=ftd_hpe_ports, ex=(0.2, 1), en=(1, 0.3))
    p.link(ftd, hpe, "STATE/FAILOVER V201", C_HA, dashed=1, src="Po1<br/>Eth1/11, Eth1/12", dst=fail_ports, ex=(0.8, 1), en=(1, 0.7))
    p.link(hpe, far, "", C_WAN, w=4, ex=(0, 0.5), en=(1, 0.5), dst="", src="")
    p.link(hpe, far2, "BAGG36 4x10G", C_WAN, w=4, ex=(1, 0.5), en=(0, 0.5), src=hpe_bagg36)
    p.legend(1380, 80)
    return p


pB = dc("2 - Site B DC-1 L2-L3", "Site B - DC-1 : L2/L3 Detail", "C8300-R1", "", "", "TBC BANK", "SILK", "L",
        "V92,93,100-103", "Po4", "Gi1/0/24, Gi2/0/24", "Po1", ("Gi1/0/23, Gi2/0/23", "BAGG31<br/>Te1/0/31, Te2/0/31"),
        "Trunk", "FTD2110 ACTIVE<br/>(192.168.2.100)  MGMT1/1", ("Po2<br/>Gi1/0/22, Gi2/0/22",),
        "BAGG32<br/>Te1/0/32, Te2/0/32", "BAGG33<br/>Te1/0/32?, Te2/0/32? (dup in source)",
        "BAGG36<br/>Te1/0/35,36 Te2/0/35,36",
        "Te1/1/1 (Site A C9300)<br/>V1,10,30,40,203 on Te1/0/30")
pB.cells.append("")
pages.append(pB)
pC = dc("3 - Site C DC-2 L2-L3", "Site C - DC-2 : L2/L3 Detail", "C8300-R2", "", "", "MAGTI", "TBC BANK", "R",
        "V91,94,100-103", "Po4", "Gi1/0/19, Gi2/0/19", "Po1", ("Gi1/0/23, Gi2/0/23", "BAGG29<br/>Te1/0/29, Te2/0/29"),
        "V108-125,300", "FTD2110 PASSIVE<br/>(172.16.2.248)", ("Po2<br/>Gi1/0/15, Gi2/0/15",),
        "BAGG32<br/>Te1/0/7, Te2/0/7", "BAGG33<br/>Te1/0/7?, Te2/0/7? (dup in source)",
        "BAGG36<br/>Te1/0/33,34 Te2/0/33,34",
        "n/a (no uplink to Site A shown)")
pages.append(pC)

# =============================================================================
# 4. TABLES
# =============================================================================
p = Page("4 - Port-channel & VLAN tables", 1700, 1300)
p.title("Port-channel / VLAN Reference", "Extracted from the Visio topology; use as the source for config verification")
tbl = ("border=1 cellpadding=4 style='border-collapse:collapse;font-size:11px'")


def table(rows, hdr):
    h = "".join(f"<th bgcolor='#1F4E79'><font color='#FFFFFF'>{c}</font></th>" for c in hdr)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table {tbl}><tr>{h}</tr>{b}</table>"


siteA = [("C8300-R1", "Po1 Gi0/0/0,0/0/1", "C9300", "Po30 Gi1/0/30,Gi2/0/30", "10,126-127,200,202,204,206"),
         ("C8300-R2", "Po1 Gi0/0/0,0/0/1", "C9300", "Po31 Gi1/0/31,Gi2/0/31", "126-127,201-202,205-206"),
         ("PA FW1 (act)", "Po20 Eth1/2,1/4", "C9300", "Gi1/0/20,Gi2/0/21", "106-125,203,300-304 (inside)"),
         ("PA FW1 (act)", "Po21 Eth1/3,1/1", "C9300", "Gi1/0/22,Gi2/0/23", "200,201,204,205 (outside)"),
         ("PA FW2 (pas)", "Po22 Eth1/2,1/4", "C9300", "Gi1/0/21,Gi2/0/20", "106-125,203,300-304 (inside)"),
         ("PA FW2 (pas)", "Po23 Eth1/1,1/3", "C9300", "Gi1/0/23,Gi2/0/22", "200,201,204,205 (outside)"),
         ("FTD act .100", "Po10 Eth1/1,1/2", "C9300", "Po25 Gi1/0/25,Gi2/0/25", "304 outside"),
         ("FTD act .100", "Po20 Eth1/3,1/4", "C9300", "Po26 Gi1/0/26,Gi2/0/26", "304 mgmt"),
         ("FTD pas .101", "Po10 Eth1/1,1/2", "C9300", "Po27 Gi1/0/27,Gi2/0/27", "304 outside"),
         ("FTD pas .101", "Po10 Eth1/3,1/4", "C9300", "Po28 Gi1/0/28,Gi2/0/28", "304 mgmt"),
         ("9200-2#", "Po1 Gi1/0/23,24", "C9300", "Po1 Gi1/0/1,Gi2/0/1", "108-125,300"),
         ("9200-5#", "Po1 Gi1/0/23,24", "C9300", "Po2 Gi1/0/2,Gi2/0/2", "108-125,300"),
         ("9200-3#", "Po1 Gi1/0/23,24", "C9300", "Po3 Gi1/0/3,Gi2/0/3", "108-125,300"),
         ("C9300 Te1/1/1", "Te1/1/1", "Site B HPE", "Te1/0/30", "1,10,20,30,40,50,100-101,106-127,200-206,300-304")]
p.text("<b>Site A</b>" + table(siteA, ["Device", "Local ports", "Peer", "Peer ports", "VLANs"]), 20, 70, 820, 520)
siteBC = [("B: C8300-R1", "Po1 Gi0/0/0,0/0/1", "C9300", "Po4 Gi1/0/24,Gi2/0/24", "92,93,100-103"),
          ("B: C9300", "Po1 Gi1/0/23,Gi2/0/23", "HPE", "BAGG31 Te1/0/31,Te2/0/31", "Trunk"),
          ("B: C9300", "Po2 Gi1/0/22,Gi2/0/22", "FTD act", "Po2 Eth1/1,1/2", "10,30,70,100,102,103,203"),
          ("B: FTD", "Po3 Eth1/3,1/4", "HPE", "BAGG32 Te1/0/32,Te2/0/32", "Inside list"),
          ("B: FTD", "Po1 Eth1/11,1/12", "HPE", "BAGG33 (src: Te1/0/32,Te2/0/32 dup)", "201 failover"),
          ("B/C: HPE", "BAGG36 Te1/0/35,36 Te2/0/35,36", "C: HPE", "BAGG36 Te1/0/33,34 Te2/0/33,34", "trunk 4x10G"),
          ("C: C8300-R2", "Po1 Gi0/0/0,0/0/1", "C9300", "Po4 Gi1/0/19,Gi2/0/19", "91,94,100-103"),
          ("C: C9300", "Po1 Gi1/0/23,Gi2/0/23", "HPE", "BAGG29 Te1/0/29,Te2/0/29", "108-125,300"),
          ("C: C9300", "Po2 Gi1/0/15,Gi2/0/15", "FTD pas", "Po2 Eth1/1,1/2", "10,30,70,100,102,103,203"),
          ("C: FTD", "Po3 Eth1/3,1/4", "HPE", "BAGG32 Te1/0/7,Te2/0/7", "Inside list"),
          ("C: FTD", "Po1 Eth1/11,1/12", "HPE", "BAGG33 (src: Te1/0/7,Te2/0/7 dup)", "201 failover")]
p.text("<b>Sites B / C</b>" + table(siteBC, ["Device", "Local ports", "Peer", "Peer ports", "VLANs"]), 860, 70, 820, 520)
p.text("<b>Open points in the source diagram (please confirm):</b><br/>"
       "1. Site A has two switches named JIQ-OFFICE-9200-4#.<br/>"
       "2. Core-side Po numbers for 9200-4/4*/6/7/8/9 not shown.<br/>"
       "3. BAGG32 and BAGG33 use identical member ports on each HPE stack (Te1/0/32 at B, Te1/0/7 at C).<br/>"
       "4. Site B/C FTD inside VLAN list is legible only at Site C; same list reused for Site B.<br/>"
       "5. Site names (A/B/C, DC-1/DC-2) are placeholders - rename to real names.", 20, 640, 1000, 140, "fontSize=12;fontColor=#B85450;")
pages.append(p)

out = '<mxfile host="app.diagrams.net">' + "".join(pg.xml(i) for i, pg in enumerate(pages)) + "</mxfile>"
open("/home/user/Lecture/Topology-detailed.drawio", "w", encoding="utf-8").write(out)
print("ok", len(out))
