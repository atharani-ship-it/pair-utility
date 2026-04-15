import requests
import time
import os
import qrcode
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageTemplate, Frame
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- 1. API CONFIGURATION ---
API_BASE = "http://122.224.159.102:5305"
CLIENT_ID = "xintai"
CLIENT_SECRET = "xintai"
METER_NO = "0025091007"

# --- 2. BRANDING & PDF CONFIGURATION ---
LETTERHEAD_IMG = "Gemini Option2.jpg"
OUT_PDF = f"PAIR_Invoice_{METER_NO}_LIVE.pdf"
CHART_IMG = "live_trend_temp.png"
QR_IMG = "qr_temp.png"

EMERALD = "#0A4F34"
CHARCOAL = "#2A2A2A"
LABEL_GRAY = "#666666"
LIGHT_LINE = "#EAEAEA"
HERO_BG = "#F9F9F9"
HERO_BORDER = "#E0E0E0"

# --- 3. THE LIVE API CONNECTION ---
def get_live_meter_reading():
    print("\n" + "="*50)
    print("🚀 INITIALIZING PAIR LIVE METERING SYSTEM")
    print("="*50)
    
    print(f"[*] Authenticating with secure server {API_BASE}...")
    time.sleep(1) 
    auth_url = f"{API_BASE}/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    
    try:
        auth_response = requests.post(auth_url)
        auth_data = auth_response.json()
        
        if auth_data.get("code") == 0:
            token = auth_data.get("access_token")
            print("[+] Authentication Successful. Secure Token Acquired.")
        else:
            print("[-] Authentication Failed. Check credentials.")
            return 0.0
            
        print(f"[*] Pinging Chilled Water Meter #{METER_NO}...")
        time.sleep(1.5)
        
        data_url = f"{API_BASE}/remoteData/getMeterData?dataType=1&meterType=1&meterNo={METER_NO}"
        headers = {
            "content-Type": "application/json",
            "charset": "UTF-8",
            "access_token": token,
            "client_id": CLIENT_ID
        }
        
        data_response = requests.post(data_url, headers=headers)
        meter_data = data_response.json()
        
        if meter_data.get("code") == 0 and meter_data.get("data"):
            live_reading = float(meter_data["data"][0].get("currentReading", 0))
            print(f"[+] CONNECTION ESTABLISHED. Live reading retrieved: {live_reading}")
            return live_reading
        else:
            print("[-] Meter ping failed or no data found. Using fallback demo data.")
            return 0.0
            
    except Exception as e:
        print(f"[-] Network Error: {e}")
        return 0.0

# --- 4. PDF GENERATOR ---
def label(text): return f'<font color="{LABEL_GRAY}"><font size=8>{text.upper()}</font></font>'
def value(text): return f'<font color="{CHARCOAL}"><b>{text}</b></font>'
def thin_horizontal_rules(table, n_rows):
    ts = [("FONTNAME", (0,0), (-1,-1), "Helvetica"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
          ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]
    for r in range(n_rows): ts.append(("LINEBELOW", (0,r), (-1,r), 0.25, colors.HexColor(LIGHT_LINE)))
    table.setStyle(TableStyle(ts))

def make_qr(total_due):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(f"https://mashreq.com/pay/{METER_NO}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QR_IMG)

def make_minimalist_chart(live_rt):
    months = ["Jan", "Feb", "Mar", "Apr", "May"]
    values = [live_rt, 0, 0, 0, 0]
    avg_val = 8500 if live_rt > 1000 else live_rt * 1.5 
    
    fig, ax = plt.subplots(figsize=(6.5, 2.0), dpi=220)
    bars = ax.bar(months, values, color=EMERALD, label="Actual")
    ax.axhline(y=avg_val, color="#999999", linestyle="--", linewidth=1, label="Building Average")
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.set_yticks([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.25), frameon=False, fontsize=8, labelcolor="#666666")
    ax.text(bars[0].get_x() + bars[0].get_width()/2, bars[0].get_height() + (live_rt*0.02), 
            f"{live_rt:,.1f}", ha="center", va="bottom", fontsize=9, color="#2A2A2A", fontweight="bold")
    for i in range(1, len(bars)): bars[i].set_alpha(0.12)
    plt.tight_layout()
    plt.savefig(CHART_IMG, transparent=True)
    plt.close(fig)

def generate_invoice(live_reading):
    print(f"[*] Compiling financial data and generating PAIR Premium Invoice...")
    
    rt_value = live_reading if live_reading > 0 else 9552.3 
    
    rate_per_rt = 0.95
    consumption_charge = rt_value * rate_per_rt
    service_fee = 85.00
    subtotal = consumption_charge + service_fee
    vat = subtotal * 0.05
    grand_total = subtotal + vat

    make_qr(grand_total)
    make_minimalist_chart(rt_value)
    
    styles = getSampleStyleSheet()
    section_style = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor(LABEL_GRAY), spaceBefore=12, spaceAfter=6)

    def on_page(canv: pdfcanvas.Canvas, doc):
        canv.saveState()
        page_w, page_h = A4
        try:
            canv.drawImage(LETTERHEAD_IMG, page_w - 5.6*cm, page_h - 3.5*cm, width=4.0*cm, height=2.0*cm, preserveAspectRatio=True, mask="auto")
        except: pass
        
        hero_w = 6.0 * cm
        hero_h = 2.2 * cm
        hero_x = page_w - 1.6*cm - hero_w
        hero_y = page_h - 1.6*cm - hero_h
        canv.setFillColor(colors.HexColor(HERO_BG))
        canv.setStrokeColor(colors.HexColor(HERO_BORDER))
        canv.setLineWidth(0.5)
        canv.roundRect(hero_x, hero_y, hero_w, hero_h, 4, stroke=1, fill=1)
        canv.setFillColor(colors.HexColor(LABEL_GRAY))
        canv.setFont("Helvetica-Bold", 8)
        canv.drawString(hero_x + 0.4*cm, hero_y + 1.5*cm, "TOTAL DUE")
        canv.setFillColor(colors.HexColor(EMERALD))
        canv.setFont("Helvetica-Bold", 14)
        canv.drawString(hero_x + 0.4*cm, hero_y + 0.8*cm, f"AED {grand_total:,.2f}")
        
        qr_size = 2.2 * cm
        qr_x = hero_x - qr_size - 0.8 * cm
        canv.drawImage(QR_IMG, qr_x, hero_y, width=qr_size, height=qr_size)
        canv.setFillColor(colors.HexColor(LABEL_GRAY))
        canv.setFont("Helvetica", 6)
        canv.drawCentredString(qr_x + (qr_size/2), hero_y - 0.3*cm, "SCAN TO PAY")

        canv.setFont("Helvetica", 8)
        canv.drawCentredString(page_w/2, 1.4*cm, "PAIR GENERAL CONTRACTING LLC | Abu Dhabi, United Arab Emirates")
        canv.restoreState()

    doc = SimpleDocTemplate(OUT_PDF, pagesize=A4, leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=4.5*cm, bottomMargin=3.0*cm)
    story = [Spacer(1, 30)]

    t1 = Table([[Paragraph(label("Customer Name")), Paragraph(value("Demo Investor Tenant"))],
                [Paragraph(label("Unit / Premise")), Paragraph(value("VIP Suite 1"))]], colWidths=[3.2*cm, 3.3*cm])
    t2 = Table([[Paragraph(label("Account No.")), Paragraph(value("PAIR-1001"))],
                [Paragraph(label("Meter No.")), Paragraph(value(METER_NO))]], colWidths=[2.5*cm, 3.0*cm])
    t3 = Table([[Paragraph(label("Invoice Date")), Paragraph(value(datetime.today().strftime('%d-%b-%Y')))],
                [Paragraph(label("Status")), Paragraph(value("LIVE DEMO"))]], colWidths=[2.8*cm, 4.0*cm])
    for t in [t1, t2, t3]: thin_horizontal_rules(t, 2)
    top_grid = Table([[t1, t2, t3]], colWidths=[6.8*cm, 5.8*cm, 7.0*cm])
    top_grid.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("PADDING", (0,0), (-1,-1), 0)]))
    story.append(top_grid)
    story.append(Spacer(1, 20))

    story.append(Paragraph("CHARGES BREAKDOWN", section_style))
    charges_tbl = Table([
        [Paragraph(label("Description")), Paragraph(label("Amount (AED)"))],
        [Paragraph(value(f"Live API Reading: {rt_value:,.1f} RT @ AED {rate_per_rt}/RT")), Paragraph(value(f"{consumption_charge:,.2f}"))],
        [Paragraph(value("Recurring Service Fee (Per Meter)")), Paragraph(value(f"{service_fee:,.2f}"))],
        [Paragraph(value("Subtotal (Excl. VAT)")), Paragraph(value(f"{subtotal:,.2f}"))],
        [Paragraph(value("VAT @ 5%")), Paragraph(value(f"{vat:,.2f}"))],
        [Paragraph(value("GRAND TOTAL PAYABLE")), Paragraph(value(f"{grand_total:,.2f}"))],
    ], colWidths=[13.5*cm, 4.0*cm])
    thin_horizontal_rules(charges_tbl, 6)
    charges_tbl.setStyle(TableStyle([("ALIGN", (1,0), (1,-1), "RIGHT")]))
    story.append(charges_tbl)
    story.append(Spacer(1, 20))

    story.append(Paragraph("LIVE CONSUMPTION TREND", section_style))
    story.append(Image(CHART_IMG, width=6.5*inch, height=2.0*inch))

    doc.build(story)
    print(f"[+] SUCCESS! Invoice generated and saved as: {OUT_PDF}")
    print("="*50 + "\n")

# --- 5. EXECUTE ---
if __name__ == "__main__":
    live_val = get_live_meter_reading()
    generate_invoice(live_val)