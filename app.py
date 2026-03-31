import streamlit as st
import requests
import time
import io
import qrcode
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

# ── CONFIG ────────────────────────────────────────────────────
API_BASE      = "http://122.224.159.102:5305"
CLIENT_ID     = "xintai"
CLIENT_SECRET = "xintai"
METER_NO      = "0025091007"
RTH_FACTOR    = 3.51685
RATE_PER_RTH  = 0.95
SERVICE_FEE   = 85.00
VAT_PCT       = 0.05
GREEN_MID     = "#2d6a4f"

st.set_page_config(page_title="PAIR Utility Platform", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.stApp{background:#f8fafb}
section[data-testid="stSidebar"]{background:#1a3d2b!important}
section[data-testid="stSidebar"] *{color:white!important}
div[data-testid="metric-container"]{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px}
.stTabs [data-baseweb="tab-list"]{background:white;border-radius:8px;padding:4px;border:1px solid #e5e7eb}
.stTabs [aria-selected="true"]{background-color:#2d6a4f!important;color:white!important}
.stButton>button{background:#2d6a4f;color:white;border:none;border-radius:6px;font-weight:600}
.stButton>button:hover{background:#1a3d2b;color:white}
.pair-card{background:white;border-radius:10px;padding:20px;border:1px solid #e5e7eb;margin:8px 0}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────
if "token"        not in st.session_state: st.session_state.token        = None
if "token_expiry" not in st.session_state: st.session_state.token_expiry = 0
if "demo_mode"    not in st.session_state: st.session_state.demo_mode    = False

# ── API ───────────────────────────────────────────────────────
def get_token():
    now = time.time()
    if st.session_state.token and now < st.session_state.token_expiry - 300:
        return st.session_state.token
    url = f"{API_BASE}/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    hdrs = {"User-Agent":"PostmanRuntime/7.32.3","Accept":"application/json","content-Type":"application/json","charset":"UTF-8"}
    try:
        res  = requests.post(url, headers=hdrs, timeout=20)
        data = res.json()
        if data.get("code") == 0:
            st.session_state.token        = data["access_token"]
            st.session_state.token_expiry = now + int(data.get("expires_in", 7200))
            return st.session_state.token
    except Exception as e:
        st.sidebar.error(f"Auth error: {e}")
    return None

def api_hdrs(token):
    return {"content-Type":"application/json","charset":"UTF-8","access_token":token,"client_id":CLIENT_ID,"User-Agent":"PostmanRuntime/7.32.3","Accept":"application/json"}

def get_live():
    if st.session_state.demo_mode:
        time.sleep(1.2)
        kwh = 97170 + random.uniform(0, 80)
        return {"kwh":kwh,"rth":kwh/RTH_FACTOR,"valve":1,"read_time":datetime.now().strftime("%d %b %Y %H:%M")}
    token = get_token()
    if not token: return None
    url = f"{API_BASE}/remoteData/getMeterData?dataType=1&meterType=1&meterNo={METER_NO}"
    try:
        res  = requests.post(url, headers=api_hdrs(token), timeout=20)
        data = res.json()
        if data.get("code") == 0 and data.get("data"):
            r  = data["data"][0]
            kwh = float(r.get("currentReading", 0))
            ts  = r.get("sysReadTime", "")
            rt  = ""
            if ts:
                try: rt = datetime.fromtimestamp(int(ts)).strftime("%d %b %Y %H:%M")
                except: rt = str(ts)
            return {"kwh":kwh,"rth":kwh/RTH_FACTOR,"valve":r.get("valveState",1),"read_time":rt}
    except Exception as e:
        st.error(f"Error: {e}")
    return None

def get_historical(s, e):
    if st.session_state.demo_mode:
        time.sleep(1.2)
        # Return correct readings based on the date range selected
        sm = s.month; sy = s.year
        if sy == 2025 and sm == 12:
            return {"prev_kwh":20980,"curr_kwh":27630,"usage_kwh":6650,"usage_rth":6650/RTH_FACTOR}
        elif sy == 2026 and sm == 1:
            return {"prev_kwh":28410,"curr_kwh":62020,"usage_kwh":33610,"usage_rth":33610/RTH_FACTOR}
        elif sy == 2026 and sm == 2:
            return {"prev_kwh":63710,"curr_kwh":97170,"usage_kwh":33460,"usage_rth":33460/RTH_FACTOR}
        else:
            return {"prev_kwh":63710,"curr_kwh":97170,"usage_kwh":33460,"usage_rth":33460/RTH_FACTOR}
    token = get_token()
    if not token: return None
    url = (f"{API_BASE}/remoteData/getMeterData?dataType=2&meterType=1&meterNo={METER_NO}"
           f"&beginTime={s.strftime('%Y-%m-%d 00:00:00')}&endTime={e.strftime('%Y-%m-%d 23:59:59')}")
    try:
        res  = requests.post(url, headers=api_hdrs(token), timeout=30)
        data = res.json()
        if data.get("code") == 0 and data.get("data"):
            readings = [float(r.get("currentReading",0)) for r in data["data"]]
            if readings:
                prev = min(readings); curr = max(readings); usage = curr - prev
                return {"prev_kwh":prev,"curr_kwh":curr,"usage_kwh":usage,"usage_rth":usage/RTH_FACTOR}
    except Exception as e:
        st.error(f"Error: {e}")
    return None

def set_valve(state):
    token = get_token()
    if not token: return False
    url = f"{API_BASE}/remoteData/setValveState?meterNo={METER_NO}&valveState={state}"
    try:
        res  = requests.post(url, headers=api_hdrs(token), timeout=20)
        return res.json().get("code") == 0
    except: return False

def calc(rth):
    cons = rth * RATE_PER_RTH; sub = cons + SERVICE_FEE
    vat  = sub * VAT_PCT;      grand = sub + vat
    return {"cons":cons,"sub":sub,"vat":vat,"grand":grand}

def make_chart():
    months = ["Dec '25","Jan '26","Feb '26"]
    values = [1890.90, 9556.85, 9514.20]
    fig, ax = plt.subplots(figsize=(7,2.5), dpi=150)
    clrs = ["#2d6a4f" if i==2 else "#d8f3dc" for i in range(3)]
    bars = ax.bar(months, values, color=clrs, width=0.5, zorder=3)
    for bar, val, cl in zip(bars, values, clrs):
        tc = "white" if cl=="#2d6a4f" else "#374151"
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*0.5,
                f"{val:,.0f}", ha="center", va="center", fontsize=8.5, color=tc, fontweight="bold")
    ax.set_ylim(0, max(values)*1.3); ax.set_yticks([])
    for sp in ["top","right","left"]: ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(axis="x", labelsize=9, colors="#6b7280")
    ax.set_facecolor("none"); fig.patch.set_alpha(0)
    plt.tight_layout(pad=0.3)
    buf = io.BytesIO()
    plt.savefig(buf, format="PNG", transparent=True, bbox_inches="tight")
    plt.close(fig); buf.seek(0)
    return buf

def gen_pdf(inv_no, period_label, inv_date, due_date, prev_kwh, curr_kwh, nums):
    import os
    buf = io.BytesIO()
    PW, PH = A4; LM = 1.8*cm; RM = 1.8*cm; CW = PW-LM-RM
    c = pdfcanvas.Canvas(buf, pagesize=A4)

    GDARK = colors.HexColor("#1a3d2b"); GMID = colors.HexColor("#2d6a4f")
    GLIGHT= colors.HexColor("#d8f3dc"); GOLDC= colors.HexColor("#c9a84c")
    INK   = colors.HexColor("#111827"); SOFT = colors.HexColor("#6b7280")
    RULE  = colors.HexColor("#e5e7eb"); WHITE= colors.white
    REDC  = colors.HexColor("#dc2626"); REDS = colors.HexColor("#fee2e2")

    def t(text,x,y,font="Helvetica",size=9,col=None,align="left"):
        c.setFont(font,size)
        c.setFillColor(col or INK)
        s = str(text)
        if align=="right":  c.drawRightString(x,y,s)
        elif align=="center": c.drawCentredString(x,y,s)
        else: c.drawString(x,y,s)

    def hl(x,y,w,col=None,lw=0.4):
        c.setStrokeColor(col or RULE); c.setLineWidth(lw); c.line(x,y,x+w,y)

    def rf(x,y,w,h,fill): c.setFillColor(fill); c.rect(x,y,w,h,stroke=0,fill=1)

    def rr(x,y,w,h,r,fill=None,stroke=None,lw=0.5):
        if fill: c.setFillColor(fill)
        if stroke: c.setStrokeColor(stroke); c.setLineWidth(lw)
        c.roundRect(x,y,w,h,r,stroke=1 if stroke else 0,fill=1 if fill else 0)

    usage_kwh = curr_kwh - prev_kwh
    usage_rth = usage_kwh / RTH_FACTOR

    # HEADER
    hh = 3.6*cm; rf(0, PH-hh, PW, hh, GDARK)
    c.setFillColor(colors.HexColor("#40916c")); c.setFillAlpha(0.18)
    c.circle(PW-1.5*cm, PH-0.4*cm, 2.2*cm, stroke=0, fill=1); c.setFillAlpha(1)

    logo = os.path.join(os.path.dirname(__file__), "pair_logo.png")
    if os.path.exists(logo):
        try:
            c.drawImage(logo, LM, PH-hh+0.5*cm,
                       width=2.6*cm, height=1.4*cm,
                       preserveAspectRatio=True, mask="auto")
        except:
            t("PAIR", LM, PH-1.35*cm, "Helvetica-Bold", 28, WHITE)
    else:
        t("PAIR", LM, PH-1.35*cm, "Helvetica-Bold", 28, WHITE)

    t("GENERAL CONTRACTING LLC",LM,PH-2.05*cm,size=7.5,col=colors.HexColor("#ffffff88"))
    for i,ln in enumerate(["Office 6, Building 94, Musaffah Industrial Area 10, Abu Dhabi, UAE",
                            "Tel: +971 55 311 4980  |  paircontracting@gmail.com"]):
        t(ln,LM,PH-2.55*cm-i*0.32*cm,size=7,col=colors.HexColor("#ffffff66"))

    t("CHILLED WATER SERVICES",PW-RM,PH-1.1*cm,size=7.5,col=GOLDC,align="right")
    t("TAX INVOICE",PW-RM,PH-1.65*cm,font="Helvetica-Bold",size=16,col=WHITE,align="right")
    t(inv_no,PW-RM,PH-2.15*cm,font="Helvetica-Bold",size=10,col=GOLDC,align="right")
    t(f"Invoice Date: {inv_date}",PW-RM,PH-2.6*cm,size=7.5,col=colors.HexColor("#ffffff88"),align="right")
    t(f"Due Date: {due_date}",PW-RM,PH-3.0*cm,size=7.5,col=colors.HexColor("#ffffff88"),align="right")

    # STATUS BAR
    by = PH-hh-0.75*cm; rf(0,by,PW,0.75*cm,GMID)
    c.setFillColor(REDS); c.roundRect(LM,by+0.14*cm,1.3*cm,0.46*cm,3,stroke=0,fill=1)
    t("UNPAID",LM+0.65*cm,by+0.14*cm,font="Helvetica-Bold",size=6.5,col=REDC,align="center")
    t(f"Billing Period:  {period_label}",LM+1.6*cm,by+0.24*cm,size=8,col=colors.HexColor("#ffffffcc"))
    t("Previous Balance: AED 0.00",PW-RM,by+0.24*cm,size=7.5,col=colors.HexColor("#ffffffaa"),align="right")

    # BILLED TO / INVOICE DETAILS
    ct = by-0.4*cm; hw = CW/2-0.3*cm
    t("BILLED TO",LM,ct-0.3*cm,size=7,col=colors.HexColor("#9ca3af"))
    hl(LM,ct-0.45*cm,hw,GLIGHT,0.6)
    t("Takhniyat LLC",LM,ct-0.85*cm,font="Helvetica-Bold",size=13,col=INK)
    for i,(lb,vl) in enumerate([("Unit / Premise","Abu Dhabi Gate City Mall"),
                                  ("Account No.","AC-00001"),("Meter No.",METER_NO),("TRN","_______________")]):
        y2 = ct-1.45*cm-i*0.42*cm
        t(lb+":",LM,y2,size=8,col=SOFT); t(vl,LM+3.2*cm,y2,font="Helvetica-Bold",size=8,col=colors.HexColor("#374151"))

    rx = PW/2+0.3*cm
    t("INVOICE DETAILS",rx,ct-0.3*cm,size=7,col=colors.HexColor("#9ca3af"))
    hl(rx,ct-0.45*cm,hw,GLIGHT,0.6)
    for i,(lb,vl,vc) in enumerate([("Invoice Number",inv_no,GMID),("Invoice Date",inv_date,INK),
                                    ("Due Date",due_date,REDC),("Billing Period",period_label,INK),("Meter Size","DN50",INK)]):
        y2 = ct-0.85*cm-i*0.42*cm
        t(lb,rx,y2,size=8,col=SOFT); t(vl,PW-RM,y2,font="Helvetica-Bold",size=8,col=vc,align="right")

    dy = ct-3.5*cm; hl(LM,dy,CW)

    # METER READINGS
    sy = dy-0.5*cm
    c.setFillColor(colors.HexColor("#40916c")); c.circle(LM+0.1*cm,sy+0.15*cm,0.12*cm,stroke=0,fill=1)
    t("METER READING DETAILS",LM+0.4*cm,sy,font="Helvetica-Bold",size=8,col=GMID)
    hl(LM+4.8*cm,sy+0.2*cm,CW-4.8*cm,GLIGHT,0.5)
    my = sy-0.55*cm
    for lb,vl,hi in [("Previous Reading (kWh)",f"{prev_kwh:,.0f}",False),
                     ("Current Reading (kWh)",f"{curr_kwh:,.0f}",False),
                     ("Consumption (kWh)",f"{usage_kwh:,.0f}",False),
                     ("Cooling Consumption (RTh)  \u00f7 3.51685",f"{usage_rth:,.2f} RTh",True)]:
        vc2 = GMID if hi else INK; vf2 = "Helvetica-Bold" if hi else "Helvetica"
        t(lb,LM+0.3*cm,my,size=8.5,col=colors.HexColor("#374151"))
        t(vl,PW-RM,my,font=vf2,size=9.5 if hi else 8.5,col=vc2,align="right")
        hl(LM,my-0.2*cm,CW); my -= 0.52*cm

    # CHARGES
    s2y = my-0.3*cm
    c.setFillColor(colors.HexColor("#40916c")); c.circle(LM+0.1*cm,s2y+0.15*cm,0.12*cm,stroke=0,fill=1)
    t("CHARGES BREAKDOWN",LM+0.4*cm,s2y,font="Helvetica-Bold",size=8,col=GMID)
    hl(LM+4.1*cm,s2y+0.2*cm,CW-4.1*cm,GLIGHT,0.5)
    thy = s2y-0.5*cm
    t("DESCRIPTION",LM+0.3*cm,thy,size=7.5,col=colors.HexColor("#9ca3af"))
    t("AMOUNT (AED)",PW-RM,thy,size=7.5,col=colors.HexColor("#9ca3af"),align="right")
    hl(LM,thy-0.2*cm,CW,colors.HexColor("#9ca3af"),1.0)
    cry = thy-0.6*cm
    for mn,sb,am in [("Chilled Water Consumption",
                      f"{usage_rth:,.2f} RTh \u00d7 AED 0.95 / RTh",f"{nums['cons']:,.2f}"),
                     ("Recurring Service Fee","Per meter / per month",f"{SERVICE_FEE:.2f}")]:
        t(mn,LM+0.3*cm,cry,font="Helvetica-Bold",size=8.5,col=INK)
        t(sb,LM+0.3*cm,cry-0.32*cm,size=7.5,col=colors.HexColor("#9ca3af"))
        t(am,PW-RM,cry,font="Helvetica-Bold",size=8.5,col=INK,align="right")
        hl(LM,cry-0.56*cm,CW); cry -= 0.78*cm

    toy = cry-0.1*cm
    t("Subtotal (Excl. VAT)",LM+0.3*cm,toy,size=8.5,col=SOFT)
    t(f"AED {nums['sub']:,.2f}",PW-RM,toy,font="Helvetica-Bold",size=8.5,col=INK,align="right")
    hl(LM,toy-0.22*cm,CW); toy -= 0.5*cm
    t("VAT @ 5%",LM+0.3*cm,toy,size=8.5,col=SOFT)
    t(f"AED {nums['vat']:,.2f}",PW-RM,toy,size=8.5,col=SOFT,align="right")

    gty = toy-0.85*cm; rr(LM,gty,CW,1.15*cm,5,fill=GDARK)
    t("GRAND TOTAL PAYABLE",LM+0.5*cm,gty+0.35*cm,size=8,col=colors.HexColor("#ffffffaa"))
    t(f"AED  {nums['grand']:,.2f}",PW-RM-0.3*cm,gty+0.3*cm,font="Helvetica-Bold",size=16,col=WHITE,align="right")

    # CHART
    trend_y2 = gty-0.6*cm
    c.setFillColor(colors.HexColor("#40916c")); c.circle(LM+0.1*cm,trend_y2+0.15*cm,0.12*cm,stroke=0,fill=1)
    t("CONSUMPTION TREND (RTh)",LM+0.4*cm,trend_y2,font="Helvetica-Bold",size=8,col=GMID)
    hl(LM+5.5*cm,trend_y2+0.2*cm,CW-5.5*cm,GLIGHT,0.5)
    cb = make_chart(); ci = PILImage.open(cb); cp = "/tmp/pair_ch.png"; ci.save(cp)
    c.drawImage(cp,LM,trend_y2-2.7*cm,width=CW,height=2.5*cm,preserveAspectRatio=False,mask="auto")

    # PAY BLOCK
    py = trend_y2-3.1*cm; ph2 = 2.1*cm
    rr(LM,py,CW,ph2,6,fill=colors.HexColor("#f9fafb"),stroke=RULE,lw=0.6)
    t(f"Please settle  AED {nums['grand']:,.2f}  on or before  {due_date}.",
      LM+0.4*cm,py+1.5*cm,font="Helvetica-Bold",size=8.5,col=INK)
    t("Overdue accounts may result in suspension of chilled water services.",
      LM+0.4*cm,py+1.1*cm,size=7.5,col=SOFT)
    t(f"Pay online \u2192  pay.paircontracting.ae/invoice/{inv_no}",
      LM+0.4*cm,py+0.68*cm,size=7.5,col=GMID)
    bw2=4.5*cm; bh2=0.9*cm; bx2=PW-RM-bw2-2.8*cm; by2=py+(ph2-bh2)/2
    rr(bx2,by2,bw2,bh2,5,fill=GMID)
    t(f"PAY NOW  \u2192  AED {nums['grand']:,.2f}",bx2+bw2/2,by2+0.3*cm,
      font="Helvetica-Bold",size=7.5,col=WHITE,align="center")
    qr2 = qrcode.QRCode(box_size=8,border=1,error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr2.add_data(f"https://pay.paircontracting.ae/invoice/{inv_no}"); qr2.make(fit=True)
    qi2 = qr2.make_image(fill_color="#1a3d2b",back_color="white")
    qp2 = f"/tmp/qr_{inv_no}.png"; qi2.save(qp2)
    qs=1.8*cm; qx2=PW-RM-qs; qy2=py+(ph2-qs)/2
    c.drawImage(qp2,qx2,qy2,width=qs,height=qs,mask="auto")
    t("SCAN TO PAY",qx2+qs/2,qy2-0.28*cm,size=6,col=colors.HexColor("#9ca3af"),align="center")

    # FOOTER
    rf(0,0,PW,1.0*cm,GDARK)
    t("PAIR General Contracting LLC  |  Abu Dhabi, UAE",LM,0.38*cm,size=7,col=colors.HexColor("#ffffff66"))
    t("+971 55 311 4980  |  paircontracting@gmail.com",PW-RM,0.38*cm,size=7,col=colors.HexColor("#ffffff66"),align="right")

    c.save(); buf.seek(0)
    return buf

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    import os as _os
    _logo_path = _os.path.join(_os.path.dirname(__file__), "pair_logo.png")
    if _os.path.exists(_logo_path):
        try:
            from PIL import Image as _SPIL
            _simg = _SPIL.open(_logo_path)
            st.image(_simg, use_container_width=True)
        except:
            st.markdown("### ⚡ PAIR Utility")
    else:
        st.markdown("### ⚡ PAIR Utility")
    st.markdown("---")
    st.markdown("**Meter:** `0025091007`")
    st.markdown("**Site:** Abu Dhabi Gate City")
    st.markdown("**Tenant:** Takhniyat LLC")
    st.markdown("---")
    demo = st.toggle("Demo Mode", value=st.session_state.demo_mode)
    st.session_state.demo_mode = demo
    if demo: st.warning("Demo mode — simulated data")
    else:    st.success("Live API mode")
    st.markdown("---")
    st.markdown("**Rate:** AED 0.95 / RTh")
    st.markdown("**Service Fee:** AED 85.00 / month")
    st.markdown("**VAT:** 5%")
    st.markdown("**Conversion:** kWh ÷ 3.51685 = RTh")

# HEADER
st.markdown("""
<div style="background:linear-gradient(135deg,#1a3d2b,#2d6a4f);color:white;
padding:20px 24px;border-radius:10px;margin-bottom:20px;">
<h2 style="color:white;margin:0;font-size:22px;">⚡ PAIR Utility Platform</h2>
<p style="color:#d8f3dc;margin:4px 0 0 0;font-size:14px;">
Abu Dhabi Gate City  |  Meter 0025091007  |  Tenant: Takhniyat LLC</p>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📡  Live Meter","🧾  Generate Invoice","🔧  Valve Control"])

# TAB 1
with tab1:
    st.markdown("### Live Meter Reading")
    st.caption("Real-time data from BTU meter hardware via supplier API.")
    if st.button("🔄  Ping Meter Now"):
        with st.spinner("Connecting to meter..."):
            r = get_live()
        if r:
            vlbl = {0:"CLOSED",1:"OPEN",2:"FORCE CLOSED",3:"FORCE OPEN",4:"UNLOCKED"}
            vok  = r["valve"] in [1,3,4]
            st.success("✅ Meter ONLINE")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Cumulative Reading", f"{r['kwh']:,.2f} kWh")
            c2.metric("Equivalent RTh",     f"{r['rth']:,.2f} RTh")
            c3.metric("Valve Status",       vlbl.get(r["valve"],"UNKNOWN"))
            c4.metric("Last Read",          r["read_time"])
        else:
            st.error("❌ Cannot reach meter. Enable Demo Mode or check network.")

# TAB 2
with tab2:
    st.markdown("### Generate Monthly Invoice")
    st.markdown("**Quick Select — Confirmed Billing Periods:**")
    q1,q2,q3 = st.columns(3)

    if "preset" not in st.session_state:
        st.session_state.preset = None

    if q1.button("CW-0001  |  Dec 2025"):
        st.session_state.preset = ("CW-0001","25 Dec 2025 – 31 Dec 2025","31 Dec 2025","30 Jan 2026",20980,27630)
    if q2.button("CW-0002  |  Jan 2026"):
        st.session_state.preset = ("CW-0002","01 Jan 2026 – 31 Jan 2026","31 Jan 2026","28 Feb 2026",28410,62020)
    if q3.button("CW-0003  |  Feb 2026"):
        st.session_state.preset = ("CW-0003","01 Feb 2026 – 28 Feb 2026","28 Feb 2026","30 Mar 2026",63710,97170)

    if st.session_state.preset:
        p = st.session_state.preset
        st.info(f"✅ Selected: **{p[0]}** — {p[1]}  |  Grand Total will be calculated on generate")

    st.markdown("---")
    st.markdown("**Or enter custom period:**")
    cc1,cc2 = st.columns(2)
    sd = cc1.date_input("Start Date", datetime(2026,3,1).date())
    ed = cc2.date_input("End Date",   datetime(2026,3,31).date())
    ino = st.text_input("Invoice Number", "CW-0004")

    if st.button("⚡  Generate Invoice", use_container_width=True):
        if st.session_state.preset:
            inv_no,period_label,inv_date,due_date,prev_kwh,curr_kwh = st.session_state.preset
            usage_kwh = curr_kwh-prev_kwh; usage_rth = usage_kwh/RTH_FACTOR
        else:
            with st.spinner("Pulling readings from API..."):
                h = get_historical(sd, ed)
            if not h:
                st.error("No data. Enable Demo Mode or use Quick Select."); st.stop()
            prev_kwh=h["prev_kwh"]; curr_kwh=h["curr_kwh"]
            usage_kwh=h["usage_kwh"]; usage_rth=h["usage_rth"]
            inv_no=ino; period_label=f"{sd.strftime('%d %b %Y')} – {ed.strftime('%d %b %Y')}"
            inv_date=ed.strftime("%d %b %Y")
            # Due date = last day of following month
            if ed.month == 12:
                due = ed.replace(year=ed.year+1, month=1, day=28)
            else:
                import calendar
                last_day = calendar.monthrange(ed.year, ed.month+1)[1]
                due = ed.replace(month=ed.month+1, day=last_day)
            due_date = due.strftime("%d %b %Y")

        nums = calc(usage_rth)
        st.success("✅ Invoice calculated")
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("Opening Read",  f"{prev_kwh:,.0f} kWh")
        r2.metric("Closing Read",  f"{curr_kwh:,.0f} kWh")
        r3.metric("Consumption",   f"{usage_rth:,.2f} RTh")
        r4.metric("Grand Total",   f"AED {nums['grand']:,.2f}")

        st.markdown(f"""<div class="pair-card">
        <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr><td style="color:#6b7280;padding:6px 0">Consumption Charge ({usage_rth:,.2f} RTh × AED 0.95)</td>
            <td align="right"><b>AED {nums['cons']:,.2f}</b></td></tr>
        <tr><td style="color:#6b7280;padding:6px 0">Recurring Service Fee</td>
            <td align="right"><b>AED {SERVICE_FEE:.2f}</b></td></tr>
        <tr><td style="color:#6b7280;padding:6px 0">Subtotal (Excl. VAT)</td>
            <td align="right"><b>AED {nums['sub']:,.2f}</b></td></tr>
        <tr><td style="color:#6b7280;padding:6px 0">VAT @ 5%</td>
            <td align="right"><b>AED {nums['vat']:,.2f}</b></td></tr>
        <tr style="border-top:2px solid #2d6a4f;"><td style="padding:8px 0">
            <b style="color:#1a3d2b;font-size:16px;">GRAND TOTAL</b></td>
            <td align="right"><b style="color:#1a3d2b;font-size:16px;">AED {nums['grand']:,.2f}</b></td></tr>
        </table></div>""", unsafe_allow_html=True)

        with st.spinner("Generating PDF..."):
            pdf = gen_pdf(inv_no,period_label,inv_date,due_date,prev_kwh,curr_kwh,nums)
        st.download_button(
            label=f"📄  Download {inv_no}  —  AED {nums['grand']:,.2f}",
            data=pdf, file_name=f"PAIR_{inv_no}_Takhniyat.pdf",
            mime="application/pdf", use_container_width=True)

# TAB 3
with tab3:
    st.markdown("### Remote Valve Control")
    st.caption("Control chilled water valve for meter 0025091007.")
    st.warning("⚠️ This directly affects tenant cooling. Use with caution.")
    vc1,vc2 = st.columns(2)
    if vc1.button("🟢  OPEN — Restore Service", use_container_width=True):
        if st.session_state.demo_mode:
            st.success("Demo: Valve OPEN command sent.")
        else:
            with st.spinner("Sending command..."): ok = set_valve(1)
            if ok: st.success("✅ Valve OPEN. Cooling restored.")
            else:  st.error("❌ Command failed.")
    if vc2.button("🔴  CLOSE — Suspend Service", use_container_width=True):
        if st.session_state.demo_mode:
            st.warning("Demo: Valve CLOSE command sent.")
        else:
            with st.spinner("Sending command..."): ok = set_valve(0)
            if ok: st.warning("⚠️ Valve CLOSED. Service suspended.")
            else:  st.error("❌ Command failed.")
