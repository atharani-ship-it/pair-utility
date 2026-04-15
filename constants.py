from decimal import Decimal

# ── Meter API ─────────────────────────────────────────────────────────────────
API_BASE_URL      = "http://122.224.159.102:5305"
API_CLIENT_ID     = "xintai"
API_CLIENT_SECRET = "xintai"
API_METER_NO      = "0025091007"
API_USER_AGENT    = "PostmanRuntime/7.32.3"
API_TIMEOUT       = 30  # seconds

# ── Billing rates ─────────────────────────────────────────────────────────────
RTH_CONVERSION_FACTOR = Decimal("3.51685")
RATE_PER_RTH          = Decimal("0.95")
SERVICE_FEE           = Decimal("85.00")
VAT_RATE              = Decimal("0.05")

# ── Token management ──────────────────────────────────────────────────────────
TOKEN_REFRESH_BUFFER  = 300  # seconds
