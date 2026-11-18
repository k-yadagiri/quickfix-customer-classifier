"""The exact label sets and safety words from the assignment."""

INTENTS = (
    "book_service",
    "reschedule",
    "cancel",
    "complaint",
    "price_enquiry",
    "status_check",
    "other",
)

CATEGORIES = (
    "plumbing",
    "electrical",
    "ac_repair",
    "appliance_repair",
    "cleaning",
    "pest_control",
    "carpentry",
    "painting",
    "none",
)

URGENCIES = ("high", "normal", "low")

# If any of these appear in the message (case-insensitive) urgency is "high".
SAFETY_KEYWORDS = (
    "spark",
    "short circuit",
    "burning",
    "smoke",
    "fire",
    "shock",
    "gas leak",
    "gas smell",
    "flooding",
    "current kottindi",
    "పొగ",
    "మంట",
    "షాక్",
)

# Intents that get "low" urgency (when there is no safety problem).
LOW_URGENCY_INTENTS = ("price_enquiry", "cancel", "other")
