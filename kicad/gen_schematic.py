import uuid, math, re, os

BASE   = os.path.dirname(os.path.abspath(__file__))
OUT    = f"{BASE}/edu-01.kicad_sch"
SYMDIR = f"{BASE}/gen/sym"   # symbol blocks extracted from the installed KiCad 10 libs
SCH_UUID = str(uuid.uuid4())
GRID = 1.27

def u(): return str(uuid.uuid4())
def G(v): return round(round(v/GRID)*GRID, 4)
def P(x,y): return (G(x),G(y))
# KiCad lib symbol offsets have +y DOWN vs the sheet's +y UP.
def rot(dx, dy, a):
    r = math.radians(a)
    return (dx*math.cos(r) - dy*math.sin(r), -(dx*math.sin(r) + dy*math.cos(r)))

PINS = {
 "Device:R": {1:{"1":(0,3.81),"2":(0,-3.81)}},
 "Device:C": {1:{"1":(0,3.81),"2":(0,-3.81)}},
 "Device:C_Polarized": {1:{"1":(0,3.81),"2":(0,-3.81)}},
 "Device:FerriteBead": {1:{"1":(0,3.81),"2":(0,-3.81)}},
 "Device:Polyfuse": {1:{"1":(0,3.81),"2":(0,-3.81)}},
 "Device:R_Potentiometer": {1:{"1":(0,3.81),"2":(3.81,0),"3":(0,-3.81)}},
 "Device:LED": {1:{"1":(-3.81,0),"2":(3.81,0)}},
 "Diode:1N4148": {1:{"1":(-3.81,0),"2":(3.81,0)}},
 "Transistor_BJT:2N3904": {1:{"1":(2.54,-5.08),"2":(-5.08,0),"3":(2.54,5.08)}},
 "Connector:TestPoint": {1:{"1":(0,0)}},
 "Connector_Generic:Conn_01x06": {1:{str(n):(-5.08,5.08-2.54*(n-1)) for n in range(1,7)}},
 "Connector_Audio:AudioJack3": {1:{"R":(5.08,0),"S":(5.08,2.54),"T":(5.08,-2.54)}},
 "Amplifier_Operational:MCP6004": {
    1:{"1":(7.62,0),"2":(-7.62,-2.54),"3":(-7.62,2.54)},
    2:{"5":(-7.62,2.54),"6":(-7.62,-2.54),"7":(7.62,0)},
    3:{"8":(7.62,0),"9":(-7.62,-2.54),"10":(-7.62,2.54)},
    4:{"12":(-7.62,2.54),"13":(-7.62,-2.54),"14":(7.62,0)},
    5:{"4":(-2.54,7.62),"11":(-2.54,-7.62)},
 },
 "power:+5V":{1:{"1":(0,0)}}, "power:GND":{1:{"1":(0,0)}},
 "power:PWR_FLAG":{1:{"1":(0,0)}},
}
AMP = {1:("1","3","2"), 2:("7","5","6"), 3:("8","10","9"), 4:("14","12","13")}

def lib_props(libid):
    lib, name = libid.split(":")
    fn = f"{SYMDIR}/{lib}__{name.replace('+','p')}.sym"
    t = open(fn).read()
    def pat(prop):
        m = re.search(r'\(property "%s" "(?:[^"\\]|\\.)*"\s*\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)' % prop, t)
        return (float(m.group(1)), float(m.group(2))) if m else (0,0)
    d = re.search(r'\(property "Description" "((?:[^"\\]|\\.)*)"', t)
    return pat("Reference"), pat("Value"), (d.group(1) if d else "")

symbols, wires, junctions, noconns, labels, texts = [],[],[],[],[],[]

def pin(sym, name):
    dx,dy = PINS[sym["libid"]][sym["unit"]][str(name)]
    rx,ry = rot(dx,dy,sym["a"])
    return P(sym["x"]+rx, sym["y"]+ry)

_pwrcnt = {}
def place(libid, ref, val, x, y, a=0, unit=1, fp="", desc=None):
    if ref in ("#PWR","#FLG"):
        _pwrcnt[ref] = _pwrcnt.get(ref,0)+1
        ref = "%s%04d" % (ref, _pwrcnt[ref])
    s = {"libid":libid,"ref":ref,"val":val,"x":G(x),"y":G(y),"a":a,"unit":unit,"fp":fp,"desc":desc}
    symbols.append(s); return s

def wire(*pts):
    p=[P(*q) for q in pts]
    p=[q for i,q in enumerate(p) if i==0 or q!=p[i-1]]
    if len(p)>1: wires.append(p)
def jct(*p): junctions.append(P(*p))
def nc(*p): noconns.append(P(*p))
def label(t,x,y,a=0): labels.append((t,*P(x,y),a))
def text(t,x,y,sz=1.8): texts.append((t,*P(x,y),sz))

def pwr5(x,y):  place("power:+5V","#PWR","+5V",x,y)
def gnd(x,y,a=0): place("power:GND","#PWR","GND",x,y,a)
def vref(x,y,a=0): label("VREF",x,y,0)   # local label: U3C output drives this net
def pflag(x,y): place("power:PWR_FLAG","#FLG","PWR_FLAG",x,y)

FPR = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
FPC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_1U = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_10U = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
FP_100U = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
F_DIP = "Package_DIP:DIP-14_W7.62mm_Socket"
F_Q = "Package_TO_SOT_THT:TO-92_Inline"
F_D = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
F_LED = "LED_THT:LED_D3.0mm"
F_TP = "TestPoint:TestPoint_Loop_D2.60mm_Drill0.9mm_Beaded"
F_HD = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
F_JK = "Connector_Audio:Jack_3.5mm_CUI_SJ1-3533NG_Horizontal"
F_POT = "Potentiometer_THT:Potentiometer_Alpha_RD901F-40-00D_Single_Vertical"
F_POT2 = "Potentiometer_THT:Potentiometer_Alpha_RD902F-40-00D_Dual_Vertical"

# ================= POWER (top-left strip) =================
# J1 unrotated: pin1 lands at (39.37, y-5.08); put VBUS rail at that level.
JY = 135
J1 = place("Connector_Generic:Conn_01x06","J1","USB-C breakout",45,JY,0,1,F_HD)
j1p = {n:pin(J1,n) for n in range(1,7)}
vy = j1p[1][1]   # VBUS level
gy = j1p[2][1]   # GND level
F1 = place("Device:Polyfuse","F1","500mA",58,vy,90,1,FPC)
wire(j1p[1], pin(F1,1))
L1 = place("Device:FerriteBead","L1","600R@100MHz",72,vy,90,1,FPR)
wire(pin(F1,2), pin(L1,1))
wire(pin(L1,2), (84,vy)); pwr5(84,vy); pflag(81,vy)
TP1 = place("Connector:TestPoint","TP1","+5V",88,vy,0,1,F_TP)
wire((84,vy), pin(TP1,1))
label("VBUS", 43,vy)
wire(j1p[2],(34,gy)); gnd(34,gy); pflag(36,gy)
TP9 = place("Connector:TestPoint","TP9","GND",37,125,0,1,F_TP)
wire((37,gy),(37,125),pin(TP9,1)); jct(37,gy)
for n in (3,4,5,6): nc(*j1p[n])
text("USB-C breakout: 1=VBUS 2=GND | CC1/CC2: 5.1k to GND each (unless on breakout) | D+/D- NC", 60, 121, 1.5)

C1 = place("Device:C_Polarized","C1","100uF",62,115,0,1,FP_100U)
wire(pin(C1,2),(62,120)); pwr5(62,120)          # pin2 = + under flip? -> check: pin2 at top
wire(pin(C1,1),(62,108)); gnd(62,108)
C2 = place("Device:C","C2","100n",74,115,0,1,FPC)
wire(pin(C2,2),(74,120)); pwr5(74,120)
wire(pin(C2,1),(74,108)); gnd(74,108)

R1 = place("Device:R","R1","1.5k",98,118,0,1,FPR)
wire(pin(R1,2),(98,125)); pwr5(98,125)
D1 = place("Device:LED","D1","PWR",98,108,90,1,F_LED)
wire(pin(R1,1), pin(D1,2))          # R -> LED anode (pin2)
wire(pin(D1,1),(98,102)); gnd(98,102)  # cathode -> GND

# ---- VREF divider + buffer (top-right) ----
R2 = place("Device:R","R2","10k",195,140,0,1,FPR)
wire(pin(R2,2),(195,147)); pwr5(195,147)
R3 = place("Device:R","R3","10k",195,122,0,1,FPR)
wire(pin(R2,1), pin(R3,2)); jct(195,128.73)
wire(pin(R3,1),(195,115)); gnd(195,115)
C3 = place("Device:C_Polarized","C3","10uF",204,124,0,1,FP_10U)
wire((195,128.73),(204,128.73),pin(C3,2))
wire(pin(C3,1),(204,118)); gnd(204,118)
U3C = place("Amplifier_Operational:MCP6004","U3","MCP6004",230,135,0,3,F_DIP)
o8,pi,mi = (pin(U3C,n) for n in AMP[3])
wire((195,128.73),(214,128.73),(214,pi[1]),pi)
wire(o8,(253,135)); vref(253,135)
wire((243,135),(243,mi[1]),mi); jct(243,135)
C4 = place("Device:C","C4","100n",258,128,0,1,FPC)
wire(pin(C4,2),(258,135)); jct(258,135)
wire(pin(C4,1),(258,121)); gnd(258,121)
TP2 = place("Connector:TestPoint","TP2","VREF",262,135,0,1,F_TP)
wire((253,135),pin(TP2,1))

# IC supply pins + decoupling (top strip); unit5 at a=180 so VDD lands on top
for ref,cn,x in [("U1","C14",280),("U2","C15",300),("U3","C16",320)]:
    ue = place("Amplifier_Operational:MCP6004",ref,"MCP6004",x,140,180,5,F_DIP)
    c  = place("Device:C",cn,"100n",x+14,140,0,1,FPC)
    p4,p11 = pin(ue,4), pin(ue,11)        # a=180: p4 top, p11 bottom
    c2p,c1p = pin(c,2), pin(c,1)
    wire(p4,(p4[0],149.86)); pwr5(p4[0],149.86)
    wire(p11,(p11[0],129.54)); gnd(p11[0],129.54)
    wire(c2p,(c2p[0],149.86),(p4[0],149.86))
    wire(c1p,(c1p[0],129.54),(p11[0],129.54))
text("POWER: USB-C 5V -> +5V   |   VREF = 2.5V buffered   |   IC supply pins + 100n decouple", 160, 152, 2.2)

# ================= OSC BLOCKS =================
osc = [
 dict(rv_t="RV1",rin="R4", ci="C5", q="Q1", d1="R5", d2="R6", rh="R7", rb="R8", cp="C6",  rv_l="RV4", rm="R9",  ui=("U1",1), ucmp=("U1",2)),
 dict(rv_t="RV2",rin="R10",ci="C7", q="Q2", d1="R11",d2="R12",rh="R13",rb="R14",cp="C8",  rv_l="RV5", rm="R15", ui=("U1",3), ucmp=("U1",4)),
 dict(rv_t="RV3",rin="R16",ci="C9", q="Q3", d1="R17",d2="R18",rh="R19",rb="R20",cp="C10", rv_l="RV6", rm="R21", ui=("U2",1), ucmp=("U2",2)),
]
YOSC = [17,62,107]   # OSC1 top .. OSC3 bottom (sheet +y renders downward)
rmix_out = {}
for i,(Y,R) in enumerate(zip(YOSC, osc)):
    # TUNE pot (unrotated): p3 top, p1 bottom, wiper right
    rvt = place("Device:R_Potentiometer",R["rv_t"],"B10k TUNE",105,Y,0,1,F_POT)
    wire(pin(rvt,3),(105,Y+7.62)); pwr5(105,Y+7.62)
    wire(pin(rvt,1),(105,Y-7.62)); vref(105,Y-7.62,180)
    rin = place("Device:R",R["rin"],"3.3k",117,Y,90,1,FPR)
    wire(pin(rvt,2), pin(rin,1))
    ui = place("Amplifier_Operational:MCP6004",R["ui"][0],"MCP6004",141,Y,0,R["ui"][1],F_DIP)
    o,pi,mi = (pin(ui,n) for n in AMP[R["ui"][1]])
    sny = mi[1]                    # -in rail (top, Y+2.54)
    wire(pin(rin,2),(125,Y),(125,sny),(137.16,sny)); jct(125,sny); jct(137.16,sny)
    # +in (bottom) -> VREF stub to the left
    wire(pi,(127,pi[1])); vref(127,pi[1],270)
    # integrating cap across SN <-> out
    ci = place("Device:C",R["ci"],"220n",141,Y+8,90,1,FPC)
    c1p,c2p = pin(ci,1), pin(ci,2)     # p1 left 137.16, p2 right 144.78
    wire(c1p,(137.16,sny))
    wire(c2p,(o[0],Y+8),o); jct(*o)
    # comparator: out right; -in TOP (158.38,Y+2.54); +in BOTTOM (158.38,Y-2.54)
    uc = place("Amplifier_Operational:MCP6004",R["ucmp"][0],"MCP6004",166,Y,0,R["ucmp"][1],F_DIP)
    co,cpi,cmi = (pin(uc,n) for n in AMP[R["ucmp"][1]])
    # SAW lane at sny level: out -> down/up to lane -> through comp -in -> toward cap
    # jog column at x=155 keeps clear of the threshold tap at x=152
    wire(o,(155,Y),(155,sny),(200,sny),(200,Y),(205,Y))
    # +in divider: rd1 top +5V, rd2 bottom GND, mid to cpi
    rd1 = place("Device:R",R["d1"],"47k",152,Y+14,0,1,FPR)
    wire(pin(rd1,2),(152,Y+21)); pwr5(152,Y+21)
    rd2 = place("Device:R",R["d2"],"10k",152,Y-2,0,1,FPR)
    wire(pin(rd1,1), pin(rd2,2)); jct(152,Y+5.19)
    wire((152,Y+5.19),(152,Y-2.54),cpi)
    wire(pin(rd2,1),(152,Y-9)); gnd(152,Y-9)
    # hysteresis: rh from cpi node up/right to co
    rh = place("Device:R",R["rh"],"1M",174,Y+7,90,1,FPR)
    wire((156,Y-2.54),(156,Y+7),pin(rh,1)); jct(156,Y-2.54)
    wire(pin(rh,2),(181,Y+7),(181,Y),co); jct(181,Y)
    rb = place("Device:R",R["rb"],"4.7k",188,Y,90,1,FPR)
    wire(co,(181,Y),pin(rb,1))
    q = place("Transistor_BJT:2N3904",R["q"],"2N3904",198,Y,0,1,F_Q)
    wire(pin(rb,2), pin(q,2))
    qe,qc = pin(q,1), pin(q,3)        # E top (+5.08), C bottom (-5.08) under flip
    # E -> SAW lane (discharges C5 on reset); C -> SN rail, routed BELOW the
    # divider GND stub (which ends at Y-9.62) to avoid touching it.
    wire(qe,(qe[0],Y+7),(196,Y+7),(196,sny)); jct(196,sny)
    wire(qc,(qc[0],Y-11),(130,Y-11),(130,sny)); jct(130,sny)
    # coupling cap pin1(+) faces SAW (left)
    cp = place("Device:C_Polarized",R["cp"],"1uF",209,Y,90,1,FP_1U)
    cp1,cp2 = pin(cp,1), pin(cp,2)
    wire((205,Y),cp1)
    # level pot p3 top <- cap; p1 bottom -> VREF; wiper -> Rm
    rvl = place("Device:R_Potentiometer",R["rv_l"],"B10k LEVEL",219,Y,0,1,F_POT)
    wire(cp2,(214,Y),(214,Y+3.81),pin(rvl,3))
    wire(pin(rvl,1),(219,Y-7.62)); vref(219,Y-7.62,180)
    rm = place("Device:R",R["rm"],"22k",231,Y,90,1,FPR)
    wire(pin(rvl,2), pin(rm,1))
    rmix_out[R["rm"]] = pin(rm,2)
    tp = place("Connector:TestPoint","TP%d"%(3+i),"SAW%d"%(i+1),203,Y+5,0,1,F_TP)
    wire((205,Y),(203,Y),(203,Y+5)); jct(203,Y)
    text("OSC%d" % (i+1), 108, Y+13, 2.0)

# ================= MIXER (U2C) =================
um = place("Amplifier_Operational:MCP6004","U2","MCP6004",266,50,0,3,F_DIP)
mo,mpi,mmo = (pin(um,n) for n in AMP[3])   # out (273.62,50); +in bottom (258.38,47.46); -in top (258.38,52.54)
sny_m = mmo[1]
for Y,R in zip(YOSC, osc):
    p2 = rmix_out[R["rm"]]
    wire(p2,(249,Y),(249,sny_m)); jct(249,Y)
wire((249,sny_m), mmo)
wire(mpi,(251,mpi[1])); vref(251,mpi[1],270)
rfm = place("Device:R","R22","22k",266,58,90,1,FPR)
f1p,f2p = pin(rfm,1), pin(rfm,2)
wire(mmo,(262,52.54),(262,57.15),f1p)
wire(f2p,(270.51,50),mo); jct(270.51,50)
TP6 = place("Connector:TestPoint","TP6","MIX",277,53,0,1,F_TP)
wire(mo,(275,50),(275,53),pin(TP6,1)); jct(275,50)
text("MIXER", 259, 62, 2.0)

# ================= CLIPPER (U2D) =================
ucp = place("Amplifier_Operational:MCP6004","U2","MCP6004",301,50,0,4,F_DIP)
cpo,cppi,cpmi = (pin(ucp,n) for n in AMP[4])  # out 308.62; -in top 293.38,52.54; +in bottom 293.38,47.46
sny_c = cpmi[1]
r23 = place("Device:R","R23","10k",284,50,90,1,FPR)
wire(mo,(275,50), pin(r23,1))
wire(pin(r23,2),(289,50),(289,sny_c),(297.19,sny_c)); jct(289,sny_c)
wire(cppi,(286,cppi[1])); vref(286,cppi[1],270)
r24 = place("Device:R","R24","20k",301,58,90,1,FPR)
f1p,f2p = pin(r24,1), pin(r24,2)
wire((297.19,sny_c),(297.19,54.19),f1p)
wire(f2p,(f2p[0],50),cpo); jct(f2p[0],50)
r25 = place("Device:R","R25","470",301,66,90,1,FPR)
k1p,k2p = pin(r25,1), pin(r25,2)
wire(k1p,(297.19,62.19),(297.19,54.19)); jct(297.19,54.19)
# clip rail: k2p -> D2.K + D3.A (bottom); D2.A + D3.K -> out (top)
D2 = place("Diode:1N4148","D2","1N4148",305,71,270,1,F_D)
D3 = place("Diode:1N4148","D3","1N4148",310,71,90,1,F_D)
d2k,d2a,d3k,d3a = pin(D2,1),pin(D2,2),pin(D3,1),pin(D3,2)
wire(k2p,d2k,d3a)
wire(d2a,d3k,(313,d2a[1]),(313,50),cpo)
clip_out_pt = (308.62,50)
TP7 = place("Connector:TestPoint","TP7","CLIP",315,53,0,1,F_TP)
wire(clip_out_pt,(315,50),(315,53),pin(TP7,1))
text("SOFT CLIP", 294, 76, 2.0)

# ================= FILTER (U3A) =================
ufa = place("Amplifier_Operational:MCP6004","U3","MCP6004",376,50,0,1,F_DIP)
fo,fpi,fmi = (pin(ufa,n) for n in AMP[1])   # out 383.62; -in TOP 368.38,52.54; +in BOTTOM 368.38,47.46
fy = fpi[1]          # 47.46 -> ladder rail level (bottom +in)
sny_f = fmi[1]       # 52.54
r26 = place("Device:R","R26","1k",325,fy,90,1,FPR)
wire(clip_out_pt,(318,50),(318,fy),pin(r26,1))
rv7a = place("Device:R_Potentiometer","RV7A","B100k CUT",335,fy,270,1,F_POT2)
wire(pin(r26,2), pin(rv7a,3))                # pin3 = left under a=270
w7a,o7a = pin(rv7a,2), pin(rv7a,1)           # wiper TOP, pin1 right
wire(w7a,(o7a[0],w7a[1]),o7a); jct(*o7a)
r27 = place("Device:R","R27","1k",345,fy,90,1,FPR)
wire(o7a, pin(r27,1))
rv7b = place("Device:R_Potentiometer","RV7B","B100k CUT",355,fy,270,1,F_POT2)
wire(pin(r27,2), pin(rv7b,3))
w7b,o7b = pin(rv7b,2), pin(rv7b,1)
wire(w7b,(o7b[0],w7b[1]),o7b); jct(*o7b)
wire(o7b, fpi)
c12 = place("Device:C","C12","22n",363,40,0,1,FPC)
wire(pin(c12,2),(pin(c12,2)[0],fy)); jct(pin(c12,2)[0],fy)
wire(pin(c12,1),(pin(c12,1)[0],34)); gnd(pin(c12,1)[0],34)
c11 = place("Device:C","C11","22n",350,58,90,1,FPC)
wire(pin(c11,1),(341,58),(341,fy)); jct(341,fy)
wire(pin(c11,2),(390,58),(390,50),fo); jct(390,50)
# -in divider to VREF + RES pot
r28 = place("Device:R","R28","10k",371,25,0,1,FPR)
g1,g2 = pin(r28,2), pin(r28,1)        # g2=pin1 bottom -> VREF; g1=pin2 top -> -in
wire(g1,(g1[0],sny_f))
wire(fmi,(372,52.54)); jct(g1[0],sny_f)   # -in rail ends at rv8 column
wire(g2,(371,18)); vref(371,18,180)
rv8 = place("Device:R_Potentiometer","RV8","B22k RES",376,60,270,1,FPR)
v1,vw,v3 = pin(rv8,1),pin(rv8,2),pin(rv8,3)  # a=270: p3 left, p1 right, wiper top
wire(v3,(v3[0],sny_f))
wire(vw,(v1[0],vw[1]),v1); jct(v1[0],vw[1])
wire(v1,(v1[0],50),fo); jct(v1[0],50)
text("FILTER  SK-LP (RV7A/B = dual gang)", 328, 63, 2.0)

# ================= OUTPUT (U3B) =================
ub = place("Amplifier_Operational:MCP6004","U3","MCP6004",400,50,0,2,F_DIP)
bo,bpi,bmi = (pin(ub,n) for n in AMP[2])    # out 407.62; +in bottom 392.38,47.46; -in top 392.38,52.54
wire(fo,(389,50),(389,bpi[1]),bpi); jct(389,50)
wire(bo,(410,50),(410,bmi[1]),bmi)
C13 = place("Device:C_Polarized","C13","10uF",417,50,90,1,FP_10U)
wire(bo, pin(C13,1))
onx = pin(C13,2)
wire(onx,(427,50)); jct(427,50)
r29 = place("Device:R","R29","100k",424,44,0,1,FPR)
wire(pin(r29,2),(424,50)); jct(424,50)
wire(pin(r29,1),(424,38)); gnd(424,38)
r30 = place("Device:R","R30","1k",434,52.54,90,1,FPR)
wire((427,50),(427,52.54),pin(r30,1))
r31 = place("Device:R","R31","1k",434,45.46,90,1,FPR)
wire((427,50),(427,45.46),pin(r31,1))
J2 = place("Connector_Audio:AudioJack3","J2","3.5mm OUT",450,50,180,1,F_JK)
wire(pin(r30,2),(pin(r30,2)[0],pin(J2,"T")[1]),pin(J2,"T"))
wire(pin(r31,2),(441,pin(r31,2)[1]),(441,pin(J2,"R")[1]),pin(J2,"R"))
wire(pin(J2,"S"),(449,pin(J2,"S")[1]),(449,47.46)); gnd(449,47.46,90)
TP8 = place("Connector:TestPoint","TP8","OUT",422,55,0,1,F_TP)
wire((427,50),(422,50),(422,55),pin(TP8,1))
text("OUT", 440, 58, 2.0)

# ================= SPARE U3D =================
ud = place("Amplifier_Operational:MCP6004","U3","MCP6004",400,20,0,4,F_DIP)
do,dpi,dmi = (pin(ud,n) for n in AMP[4])
wire(dpi,(388,dpi[1])); vref(388,dpi[1],270)
wire(do,(410,20),(410,dmi[1]),dmi)
text("U3D spare", 389, 25, 1.5)

# ================= EMIT =================
def fmt(v):
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return s if s else "0"

def emit_prop(name,val,x,y,a,hide=False):
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {fmt(x)} {fmt(y)} {a})\n'
            '\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n' +
            ('\t\t\t\t(hide yes)\n' if hide else '') +
            '\t\t\t)\n\t\t)\n')

# ---- connectivity post-pass ----------------------------------------
# KiCad connects pins/wires only at segment endpoints (and junctions).
# Split every wire segment wherever a pin endpoint, junction, or other
# wire endpoint lies strictly inside it, so every node is endpoint-joined.
conn_pts = set()
for s in symbols:
    for pn in PINS[s["libid"]][s["unit"]]:
        conn_pts.add(pin(s,pn))
conn_pts.update(junctions)
for pts in wires:
    conn_pts.update(pts)

def on_seg(p,a,b):
    (px,py),(ax,ay),(bx,by) = p,a,b
    dx,dy = bx-ax, by-ay
    if dx==0 and dy==0: return False
    if abs((px-ax)*dy - (py-ay)*dx) > 1e-6: return False
    t = ((px-ax)*dx + (py-ay)*dy)/(dx*dx+dy*dy)
    return 1e-9 < t < 1-1e-9

segs = set()
for pts in wires:
    for a,b in zip(pts,pts[1:]):
        if a!=b: segs.add((a,b))
split_segs = set()
for a,b in segs:
    mids = sorted((p for p in conn_pts if on_seg(p,a,b)),
                  key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
    cur = a
    for m in mids+[b]:
        if cur!=m: split_segs.add((cur,m))
        cur = m

body = ""
for s in symbols:
    libid=s["libid"]; a=s["a"]
    try:
        (ro,vo,desc) = lib_props(libid)
    except Exception:
        ro,vo,desc = (0,5.08),(0,-5.08),""
    if s["desc"]: desc=s["desc"]
    rx,ry = rot(ro[0],ro[1],a); vx,vy = rot(vo[0],vo[1],a)
    body += f'\t(symbol\n\t\t(lib_id "{libid}")\n\t\t(at {fmt(s["x"])} {fmt(s["y"])} {a})\n\t\t(unit {s["unit"]})\n\t\t(body_style 1)\n'
    body += '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
    body += f'\t\t(uuid "{u()}")\n'
    body += emit_prop("Reference",s["ref"],s["x"]+rx,s["y"]+ry,a,hide=s["ref"].startswith('#'))
    body += emit_prop("Value",s["val"],s["x"]+vx,s["y"]+vy,a,hide=s["ref"].startswith('#FLG'))
    for nm,vv,hd in [("Footprint",s["fp"],True),("Datasheet","",True),("Description",desc,True)]:
        body += emit_prop(nm,vv,s["x"],s["y"],a,hd)
    for pn in PINS[libid][s["unit"]]:
        body += f'\t\t(pin "{pn}"\n\t\t\t(uuid "{u()}")\n\t\t)\n'
    body += f'\t\t(instances\n\t\t\t(project "edu-01"\n\t\t\t\t(path "/{SCH_UUID}"\n\t\t\t\t\t(reference "{s["ref"]}")\n\t\t\t\t\t(unit {s["unit"]})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'

for a,b in split_segs:
    body += (f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})\n\t\t)\n'
             f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')
for x,y in set(junctions):
    body += f'\t(junction\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{u()}")\n\t)\n'
for x,y in noconns:
    body += f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(uuid "{u()}")\n\t)\n'
for t,x,y,a in labels:
    body += (f'\t(label "{t}"\n\t\t(at {fmt(x)} {fmt(y)} {a})\n\t\t(fields_autoplaced yes)\n'
             f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')
for t,x,y,sz in texts:
    body += (f'\t(text "{t}"\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {sz} {sz})\n\t\t\t\t(bold yes)\n\t\t\t)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')

def sblock(t,i):
    d=0
    for j in range(i,len(t)):
        if t[j]=='(': d+=1
        elif t[j]==')':
            d-=1
            if d==0: return j+1
    return None

def prop_blocks(t):
    out={}
    for m in re.finditer(r'\(property "((?:[^"\\]|\\.)*)"',t):
        e = sblock(t,m.start())
        out[m.group(1)]=(m.start(),e,t[m.start():e])
    return out

def flatten(libid):
    lib, name = libid.split(":")
    blk = open(f"{SYMDIR}/{lib}__{name.replace('+','p')}.sym").read().strip()
    m = re.search(r'\(extends "([^"]+)"', blk)
    if not m:
        return re.sub(r'\(symbol "'+re.escape(name)+r'"', f'(symbol "{libid}"', blk, count=1)
    pn = m.group(1)
    parent = open(f"{SYMDIR}/{lib}__{pn}.sym").read().strip()
    flat = re.sub(r'\(symbol "'+re.escape(pn)+r'"', f'(symbol "{libid}"', parent, count=1)
    flat = flat.replace(f'(symbol "{pn}_', f'(symbol "{name}_')
    # child overrides whole property blocks (value AND position/effects)
    cprops = prop_blocks(blk)
    pprops = prop_blocks(flat)
    repls = [(s,e,cprops[k][2]) for k,(s,e,_) in pprops.items() if k in cprops]
    out = flat
    for s,e,txt in sorted(repls, reverse=True):
        out = out[:s] + txt + out[e:]
    # child props missing in parent -> insert before (embedded_fonts / final )
    missing = [cprops[k][2] for k in cprops if k not in pprops]
    if missing:
        idx = out.rfind('(embedded_fonts')
        if idx<0: idx = out.rfind(')')
        add = "\n" + "\n".join(b.replace("\n","\n\t") for b in missing)
        out = out[:idx] + add + "\n\t" + out[idx:]
    return out

libfiles = {}
for s in symbols:
    libid=s["libid"]
    if libid in libfiles: continue
    libfiles[libid]=flatten(libid)

libsec = "\t(lib_symbols\n"
for k in sorted(libfiles):
    libsec += "\t\t" + libfiles[k].replace("\n","\n\t\t") + "\n"
libsec += "\t)\n"

sch = f'''(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{SCH_UUID}")
\t(paper "A2")
\t(title_block
\t\t(title "EDU-01 - Analog Drone Synth")
\t\t(date "2026-11-16")
\t\t(rev "0.1")
\t\t(company "Electronic Synapse")
\t\t(comment 1 "Educational through-hole kit - 5V USB-C supply")
\t)
{libsec}{body}\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
\t(embedded_fonts no)
)
'''
open(OUT,"w").write(sch)
print("written", OUT, len(symbols), "symbols", len(wires), "wire paths")

# ================= SKELETON PCB =================
PCB_LAYERS = '''\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
'''
pcb = f'''(kicad_pcb
\t(version 20260206)
\t(generator "pcbnew")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A3")
{PCB_LAYERS}\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t)
\t(net 0 "")
\t(gr_rect
\t\t(start 30 30)
\t\t(end 130 90)
\t\t(stroke
\t\t\t(width 0.15)
\t\t\t(type default)
\t\t)
\t\t(fill no)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{u()}")
\t)
)
'''
open(f"{BASE}/edu-01.kicad_pcb","w").write(pcb)
print("written", f"{BASE}/edu-01.kicad_pcb")
