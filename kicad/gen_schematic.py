import uuid, math, re, os

BASE   = os.path.dirname(os.path.abspath(__file__))
OUT    = f"{BASE}/edu-01.kicad_sch"
SYMDIR = f"{BASE}/gen/sym"   # symbol blocks extracted from the installed KiCad 10 libs
SCH_UUID = str(uuid.uuid4())
GRID = 1.27

def u(): return str(uuid.uuid4())
def G(v): return round(round(v/GRID)*GRID, 4)
def P(x,y): return (G(x),G(y))
# Sheet +y is DOWN. Symbol-library pin offsets have +y UP relative to the
# sheet, so rot() negates the transformed y component (verified by netlist).
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
def place(libid, ref, val, x, y, a=0, unit=1, fp="", desc=None, lr=None, lv=None):
    if ref in ("#PWR","#FLG"):
        _pwrcnt[ref] = _pwrcnt.get(ref,0)+1
        ref = "%s%04d" % (ref, _pwrcnt[ref])
    s = {"libid":libid,"ref":ref,"val":val,"x":G(x),"y":G(y),"a":a,"unit":unit,"fp":fp,"desc":desc,"lr":lr,"lv":lv}
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

# ref/value text offsets (sheet mm, +y down) per (libid, angle) — the lib
# defaults collide when a symbol is rotated
LBL = {
 ("Device:R",90):            ((0,-4.5),(0,5)),
 ("Device:R",0):             ((4.5,-1.5),(4.5,1.5)),
 ("Device:R_Potentiometer",0):((-8,-1),(-8,2)),
 ("Device:R_Potentiometer",270):((0,-5),(0,6.5)),
 ("Diode:1N4148",90):        ((0,-4.5),(0,5)),
 ("Diode:1N4148",270):       ((0,-4.5),(0,5)),
 ("Device:C",90):            ((0,-5),(0,6)),
 ("Device:C_Polarized",90):  ((0,-5),(0,6)),
 ("Device:LED",90):          ((0,-5),(0,5)),
 ("Transistor_BJT:2N3904",0):((-5,-5.5),(7,4)),
 ("Connector_Audio:AudioJack3",180):((0,-9),(0,-12)),
}

# ================= POWER (top band) =================
# J1 pins face left, pin1 = VBUS on top. +5V rail runs right at that level.
JY = 30
J1 = place("Connector_Generic:Conn_01x06","J1","USB-C breakout",45,JY,0,1,F_HD)
j1p = {n:pin(J1,n) for n in range(1,7)}
vy,gy = j1p[1][1], j1p[2][1]           # VBUS / GND pin rows
F1 = place("Device:Polyfuse","F1","500mA",54,vy,90,1,FPC)
wire(j1p[1], pin(F1,1)); label("VBUS", 41, vy)
L1 = place("Device:FerriteBead","L1","600R@100MHz",68,vy,90,1,FPR)
wire(pin(F1,2), pin(L1,1))
RAILY = vy                            # +5V rail level (~25.4)
wire(pin(L1,2),(74,RAILY)); wire((74,RAILY),(341.63,RAILY))
pwr5(74,RAILY); pflag(76,RAILY)
TP1 = place("Connector:TestPoint","TP1","+5V",80,RAILY,0,1,F_TP)
# J1 GND pin + NC pins
wire(j1p[2],(30,gy)); gnd(30,gy); pflag(33,gy)
TP9 = place("Connector:TestPoint","TP9","GND",34,18,0,1,F_TP)
wire((34,gy),(34,18),pin(TP9,1)); jct(34,gy)
for n in (3,4,5,6): nc(*j1p[n])
text("USB-C breakout: 1=VBUS 2=GND | CC 5.1k on breakout | D+/D- NC", 70, 15, 1.5)

# bulk + decoupling caps hang off the rail: pin1 (+) up to +5V, pin2 to GND
C1 = place("Device:C_Polarized","C1","100uF",84,29.21,0,1,FP_100U)
wire(pin(C1,1),(84,RAILY))
wire(pin(C1,2),(84,38)); gnd(84,38)
C2 = place("Device:C","C2","100n",92,29.21,0,1,FPC)
wire(pin(C2,1),(92,RAILY))
wire(pin(C2,2),(92,38)); gnd(92,38)

# power LED: rail -> R1 -> LED anode -> GND
R1 = place("Device:R","R1","1.5k",104,29.21,0,1,FPR)
wire(pin(R1,1),(104,RAILY))
D1 = place("Device:LED","D1","PWR",104,40,90,1,F_LED)
wire(pin(R1,2), pin(D1,2))
wire(pin(D1,1),(104,48)); gnd(104,48)

# ---- VREF divider + buffer ----
R2 = place("Device:R","R2","10k",158,29.21,0,1,FPR)
wire(pin(R2,1),(158,RAILY))
R3 = place("Device:R","R3","10k",158,41,0,1,FPR)
wire(pin(R2,2), pin(R3,1)); jct(158,35)          # divider tap
wire(pin(R3,2),(158,49)); gnd(158,49)
C3 = place("Device:C_Polarized","C3","10uF",169,40,0,1,FP_10U)
wire((158,35),(169,35),(169,pin(C3,1)[1]),pin(C3,1)); jct(169,35)
wire(pin(C3,2),(169,48)); gnd(169,48)
U3C = place("Amplifier_Operational:MCP6004","U3","MCP6004",205,38,0,3,F_DIP)
o8,pi,mi = (pin(U3C,n) for n in AMP[3])
wire((158,35),(190,35),(190,pi[1]),pi)
TP2 = place("Connector:TestPoint","TP2","VREF",234,38,0,1,F_TP)
wire(o8,pin(TP2,1)); vref(222,38); jct(218,38); jct(226,38)
wire(o8,(218,38),(218,44),(193,44),(193,mi[1]),mi)   # fb under the body
C4 = place("Device:C","C4","100n",226,43,0,1,FPC)
wire(pin(C4,1),(226,38))
wire(pin(C4,2),(226,50)); gnd(226,50)
text("VREF = 2.5V buffered (U3C)", 195, 20, 1.5)

# IC supply pins + 100n decoupling, one group per package (unit5 a=180: VDD top)
for ref,cn,x in [("U1","C14",280),("U2","C15",305),("U3","C16",330)]:
    ue = place("Amplifier_Operational:MCP6004",ref,"MCP6004",x,38,0,5,F_DIP)
    c  = place("Device:C",cn,"100n",x+12,32,0,1,FPC)
    p4,p11 = pin(ue,4), pin(ue,11)
    wire(p4,(p4[0],RAILY))
    wire(p11,(p11[0],50)); gnd(p11[0],50)
    wire(pin(c,1),(pin(c,1)[0],RAILY))
    wire(pin(c,2),(pin(c,2)[0],50),(p11[0],50))
text("IC supply pins + 100n decoupling (per package)", 280, 20, 1.5)

# ================= SPARE U3D (top-right, wired as VREF follower) =================
ud = place("Amplifier_Operational:MCP6004","U3","MCP6004",440,30,0,4,F_DIP)
do,dpi,dmi = (pin(ud,n) for n in AMP[4])
wire(dpi,(424,dpi[1])); vref(424,dpi[1],270)
wire(do,(456,30),(456,25),(429,25),(429,dmi[1]),dmi)  # fb over the top
text("U3D spare (follower)", 420, 42, 1.5)

# ================= OSC BLOCKS =================
# Per row: TUNE -> Rin -> integrator -> SAW -> comparator -> Rb -> 2N3904
# reset (E->SAW, C->summation node over the top), coupling cap -> LEVEL -> Rmix.
osc = [
 dict(rv_t="RV1",rin="R4", ci="C5", q="Q1", d1="R5", d2="R6", rh="R7", rb="R8", cp="C6",  rv_l="RV4", rm="R9",  ui=("U1",1), ucmp=("U1",2)),
 dict(rv_t="RV2",rin="R10",ci="C7", q="Q2", d1="R11",d2="R12",rh="R13",rb="R14",cp="C8",  rv_l="RV5", rm="R15", ui=("U1",3), ucmp=("U1",4)),
 dict(rv_t="RV3",rin="R16",ci="C9", q="Q3", d1="R17",d2="R18",rh="R19",rb="R20",cp="C10", rv_l="RV6", rm="R21", ui=("U2",1), ucmp=("U2",2)),
]
YOSC = [95,145,195]
rmix_out = {}
for i,(Y,R) in enumerate(zip(YOSC, osc)):
    # TUNE pot: pin1 top -> +5V, pin3 bottom -> VREF, wiper -> Rin
    rvt = place("Device:R_Potentiometer",R["rv_t"],"B10k TUNE",105,Y,0,1,F_POT)
    wire(pin(rvt,1),(105,Y-8)); pwr5(105,Y-8)
    wire(pin(rvt,3),(105,Y+8)); vref(105,Y+8,180)
    rin = place("Device:R",R["rin"],"3.3k",117,Y,90,1,FPR)
    wire(pin(rvt,2), pin(rin,1))
    # integrator: -in bottom-left = SN rail; +in top-left -> VREF
    ui = place("Amplifier_Operational:MCP6004",R["ui"][0],"MCP6004",141,Y,0,R["ui"][1],F_DIP)
    o,pi,mi = (pin(ui,n) for n in AMP[R["ui"][1]])
    ci = place("Device:C",R["ci"],"220n",141,Y+9,90,1,FPC,lr=(0,4.5),lv=(0,8))
    wire(pin(rin,2),(124,Y),(124,mi[1]),(pin(ci,1)[0],mi[1])); jct(124,mi[1])
    wire(pi,(128,pi[1])); vref(128,pi[1],270)
    # integrator cap SN <-> out (drawn below the amp)
    wire(pin(ci,1),(pin(ci,1)[0],mi[1])); jct(pin(ci,1)[0],mi[1])
    wire(pin(ci,2),(o[0],Y+9),o); jct(*o)
    # comparator + threshold divider + hysteresis
    uc = place("Amplifier_Operational:MCP6004",R["ucmp"][0],"MCP6004",176,Y,0,R["ucmp"][1],F_DIP)
    co,cpi,cmi = (pin(uc,n) for n in AMP[R["ucmp"][1]])
    # SAW: lane A integrator-out -> comp -in; lane B -> Q emitter + coupling cap
    wire(o,(153,Y),(153,cmi[1]),cmi); jct(153,cmi[1])
    # threshold divider +5V -> R5 -> tap -> R6 -> GND, tap -> comp +in rail
    rd1 = place("Device:R",R["d1"],"47k",162,Y-18,0,1,FPR)
    wire(pin(rd1,1),(162,Y-25)); pwr5(162,Y-25)
    rd2 = place("Device:R",R["d2"],"10k",162,Y-6,0,1,FPR)
    wire(pin(rd1,2), pin(rd2,1)); jct(162,Y-12)
    wire(pin(rd2,2),(162,Y+1)); gnd(162,Y+1)
    # +in node: pin -> up at 164 -> rail right to hysteresis
    wire(cpi,(164,Y-2.54),(164,Y-12),(180.19,Y-12))
    wire((162,Y-12),(164,Y-12))
    rh = place("Device:R",R["rh"],"1M",184,Y-12,90,1,FPR)
    rb = place("Device:R",R["rb"],"4.7k",190,Y,90,1,FPR)
    wire(co,pin(rb,1)); jct(*pin(rb,1))
    wire(pin(rh,2),(186.19,Y-12),pin(rb,1))
    q = place("Transistor_BJT:2N3904",R["q"],"2N3904",203,Y,0,1,F_Q)
    wire(pin(rb,2), pin(q,2))
    qe,qc = pin(q,1), pin(q,3)        # E bottom (Y+5.08), C top (Y-5.08)
    # SAW lane B below the row: -in lane jct -> Q.E -> coupling cap
    cp = place("Device:C_Polarized",R["cp"],"1uF",213,Y+8,90,1,FP_1U,lr=(0,5),lv=(0,8.5))
    wire((153,cmi[1]),(153,Y+8),pin(cp,1))
    wire(qe,(qe[0],Y+8))
    # C -> SN over the top of the row
    wire(qc,(qc[0],Y-30),(136,Y-30),(136,mi[1]))
    # LEVEL pot: signal -> pin1 top; pin3 bottom -> VREF; wiper -> Rmix
    rvl = place("Device:R_Potentiometer",R["rv_l"],"B10k LEVEL",227,Y+8,0,1,F_POT,lr=(4,-6),lv=(4,-3))
    wire(pin(cp,2),(219,Y+8),(219,pin(rvl,1)[1]),pin(rvl,1))
    wire(pin(rvl,3),(227,Y+15)); vref(227,Y+15,180)
    rm = place("Device:R",R["rm"],"22k",237,Y+8,90,1,FPR)
    wire(pin(rvl,2), pin(rm,1))
    rmix_out[R["rm"]] = pin(rm,2)
    tp = place("Connector:TestPoint","TP%d"%(3+i),"SAW%d"%(i+1),199,Y+12,0,1,F_TP)
    wire((199,Y+8),(199,Y+12)); jct(199,Y+8)
    text("OSC%d" % (i+1), 108, Y-15, 2.0)

# ================= SIGNAL CHAIN (bottom band, L->R) =================
CY = 245
# mix bus: all three Rmix outputs drain down column x=242 to the mixer -in
for Y,R in zip(YOSC, osc):
    p2 = rmix_out[R["rm"]]
    wire(p2,(242,p2[1]))
um = place("Amplifier_Operational:MCP6004","U2","MCP6004",275,CY,0,3,F_DIP)
mo,mpi,mmo = (pin(um,n) for n in AMP[3])
wire((242,YOSC[0]+8),(242,mmo[1]),mmo)
wire(mpi,(262,mpi[1])); vref(262,mpi[1],270)
rfm = place("Device:R","R22","22k",275,CY+10,90,1,FPR,lr=(0,5.5),lv=(0,9))
wire(mmo,(267.38,CY+10),pin(rfm,1))
wire(pin(rfm,2),(mo[0],CY+10),mo); jct(*mo)
TP6 = place("Connector:TestPoint","TP6","MIX",286,CY-5,0,1,F_TP)
wire((286,CY),(286,CY-5)); jct(286,CY)
text("MIXER", 262, CY+16, 2.0)

# ---- soft clip (U2D): R23 in, R24 fb, R25 + anti-parallel 1N4148 ----
ucp = place("Amplifier_Operational:MCP6004","U2","MCP6004",310,CY,0,4,F_DIP)
cpo,cppi,cpmi = (pin(ucp,n) for n in AMP[4])
r23 = place("Device:R","R23","10k",295,CY,90,1,FPR)
wire(mo,pin(r23,1)); jct(286,CY)
wire(pin(r23,2),(297,CY),(297,cpmi[1]),cpmi)
wire(cppi,(297,cppi[1])); vref(297,cppi[1],270)
r24 = place("Device:R","R24","20k",315,CY+10,90,1,FPR,lr=(5,0.5),lv=(5,3))
wire(cpmi,(302.38,CY+10),pin(r24,1))
wire(pin(r24,2),(cpo[0],CY+10),cpo); jct(*cpo)
r25 = place("Device:R","R25","470",315,CY+17,90,1,FPR,lr=(5,0.5),lv=(5,3.5))
wire(pin(r24,1),(311.19,CY+17),pin(r25,1)); jct(311.19,CY+10)
D2 = place("Diode:1N4148","D2","1N4148",325,CY+13,270,1,F_D,lr=(0,-8),lv=(0,-5.5))  # K top
D3 = place("Diode:1N4148","D3","1N4148",330,CY+13,90,1,F_D,lr=(0,-8),lv="hide")      # A top
d2k,d2a,d3k,d3a = pin(D2,1),pin(D2,2),pin(D3,1),pin(D3,2)
wire(pin(r25,2),(324,CY+17),(324,CY+19.5),(330,CY+19.5))  # bottom lane
wire(d2a,(325,CY+19.5)); wire(d3k,(330,CY+19.5))
wire(d2k,(325,CY+8.5),(330,CY+8.5),d3a)                   # top bridge
wire((327.54,CY+8.5),(327.54,CY),cpo); jct(327.54,CY+8.5)
TP7 = place("Connector:TestPoint","TP7","CLIP",322,CY-5,0,1,F_TP)
wire((322,CY),(322,CY-5)); jct(322,CY)
text("SOFT CLIP", 296, CY+22, 2.0)

# ---- Sallen-Key LP filter (U3A) ----
ufa = place("Amplifier_Operational:MCP6004","U3","MCP6004",380,CY,0,1,F_DIP)
fo,fpi,fmi = (pin(ufa,n) for n in AMP[1])
fy = fpi[1]                                # ladder rail level (top +in)
r26 = place("Device:R","R26","1k",340,fy,90,1,FPR)
wire(cpo,(333,CY),(333,fy),pin(r26,1))
rv7a = place("Device:R_Potentiometer","RV7A","B100k CUT",348,fy,270,1,F_POT2)
wire(pin(r26,2), pin(rv7a,3))
w7a,o7a = pin(rv7a,2), pin(rv7a,1)         # wiper bottom, pin1 right
wire(w7a,(pin(rv7a,3)[0],w7a[1]),pin(rv7a,3))   # wiper tied to pin3
r27 = place("Device:R","R27","1k",358,fy,90,1,FPR)
wire(o7a, pin(r27,1)); jct(*o7a)
rv7b = place("Device:R_Potentiometer","RV7B","B100k CUT",366,fy,270,1,F_POT2)
wire(pin(r27,2), pin(rv7b,3))
w7b,o7b = pin(rv7b,2), pin(rv7b,1)
wire(w7b,(pin(rv7b,3)[0],w7b[1]),pin(rv7b,3))
wire(o7b,fpi); jct(*o7b)
c12 = place("Device:C","C12","22n",374,fy-10,0,1,FPC,lr=(6,-1),lv=(6,2))  # +in node -> GND
wire(pin(c12,2),(374,fy),(371,fy)); jct(374,fy)
wire(pin(c12,1),(374,fy-14)); gnd(374,fy-14)
c11 = place("Device:C","C11","22n",354,fy+10,90,1,FPC,lr=(6,3))   # mid node -> out
wire(pin(c11,1),(352,fy+10),(352,fy)); jct(352,fy)
wire(pin(c11,2),(390,fy+10),(390,CY),fo); jct(390,CY)
# -in: R28 to VREF, RV8 (RES) to out
r28 = place("Device:R","R28","10k",374,CY+9,0,1,FPR,lr=(-4.5,-1.5),lv=(-4.5,1.5))
rv8 = place("Device:R_Potentiometer","RV8","B22k RES",382,CY+7,270,1,FPR,lr=(-3,8.5),lv=(8,4))
v3,vw,v1 = pin(rv8,3),pin(rv8,2),pin(rv8,1)  # p3 left, p1 right, wiper bottom
# -in node: left of the body, down to R28's pin1 row, right to RV8's p3
wire(fmi,(368,fmi[1]),(368,pin(r28,1)[1]),(v3[0],pin(r28,1)[1]),v3)
jct(*pin(r28,1))
wire(pin(r28,2),(374,CY+13)); vref(374,CY+13,180)
wire(vw,(v1[0],vw[1]),v1); jct(*v1)
wire(v1,(v1[0],CY),fo); jct(v1[0],CY)
text("FILTER  SK-LP 2p (RV7A/B = dual gang)", 336, CY-17, 2.0)

# ---- output buffer (U3B) + jack ----
ub = place("Amplifier_Operational:MCP6004","U3","MCP6004",410,CY,0,2,F_DIP)
bo,bpi,bmi = (pin(ub,n) for n in AMP[2])
wire(fo,(389,CY),(389,bpi[1]),bpi); jct(389,CY)
wire(bo,(421,CY),(421,CY-7),(399,CY-7),(399,bmi[1]),bmi)  # fb over the top
C13 = place("Device:C_Polarized","C13","10uF",427,CY,90,1,FP_10U)
wire(bo, pin(C13,1))
onx = pin(C13,2)
wire(onx,(433,CY)); jct(433,CY)
r29 = place("Device:R","R29","100k",434,CY+7,0,1,FPR)
wire(pin(r29,1),(434,CY))
wire(pin(r29,2),(434,CY+11)); gnd(434,CY+11)
TP8 = place("Connector:TestPoint","TP8","OUT",433,CY-7,0,1,F_TP)
wire((433,CY),(433,CY-7))
r30 = place("Device:R","R30","1k",440,CY-2.54,90,1,FPR)
wire((433,CY),(436,CY),(436,pin(r30,1)[1]),pin(r30,1))
r31 = place("Device:R","R31","1k",440,CY+2.54,90,1,FPR)
wire((433,CY),(433,CY+2.54),pin(r31,1))
J2 = place("Connector_Audio:AudioJack3","J2","3.5mm OUT",452,CY,180,1,F_JK)
wire(pin(r30,2),(445,pin(r30,2)[1]),(445,pin(J2,"T")[1]),pin(J2,"T"))
wire(pin(r31,2),(444,pin(r31,2)[1]),(444,pin(J2,"R")[1]),pin(J2,"R"))
wire(pin(J2,"S"),(449,pin(J2,"S")[1]),(449,CY+6)); gnd(449,CY+6)

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
    lo = LBL.get((libid,a), (None,None))
    if s["lr"]: rx,ry,ra = s["lr"][0],s["lr"][1],a
    elif lo[0]: rx,ry,ra = lo[0][0],lo[0][1],a
    else: rx,ry,ra = rot(ro[0],ro[1],a)+(a,)
    if s["lv"]=="hide": vx,vy,va = 0,0,0
    elif s["lv"]: vx,vy,va = s["lv"][0],s["lv"][1],a
    elif lo[1]: vx,vy,va = lo[1][0],lo[1][1],a
    else: vx,vy,va = rot(vo[0],vo[1],a)+(a,)
    body += f'\t(symbol\n\t\t(lib_id "{libid}")\n\t\t(at {fmt(s["x"])} {fmt(s["y"])} {a})\n\t\t(unit {s["unit"]})\n\t\t(body_style 1)\n'
    body += '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
    body += f'\t\t(uuid "{u()}")\n'
    body += emit_prop("Reference",s["ref"],s["x"]+rx,s["y"]+ry,ra,hide=s["ref"].startswith('#'))
    body += emit_prop("Value",s["val"],s["x"]+vx,s["y"]+vy,va,hide=s["lv"]=="hide" or s["ref"].startswith('#FLG'))
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
