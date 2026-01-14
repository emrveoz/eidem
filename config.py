import os

# AI opsiyonel (şimdilik kullanılmıyor; sonra ekleriz)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

EXPORT_HEADERS = [
    "*Action(SiteID=Germany|Country=DE|Currency=EUR|Version=1193)",
    "Custom label (SKU)",
    "Category ID",
    "Category name",
    "Title",
    "Relationship",
    "Relationship details",
    "Schedule Time",
    "P:EAN",
    "P:EPID",
    "Start price",
    "Quantity",
    "Item photo URL",
    "VideoID",
    "Condition ID",
    "Description",
    "Format",
    "Duration",
    "Buy It Now price",
    "Best Offer Enabled",
    "Best Offer Auto Accept Price",
    "Minimum Best Offer Price",
    "VAT%",

    # Custom fields (senin istediğin)
    "C:Marke",
    "C:Formulierung",
    "C:Wirksame Inhaltsstoffe",
    "C:Produktart",
    "C:Herstellernummer",
    "C:Anzahl der Tabletten",
    "C:Hauptverwendungszweck",
    "C:Inhaltsstoffe",
    "C:Versorgung",

    # Manufacturer
    "Manufacturer Name",
    "Manufacturer AddressLine1",
    "Manufacturer City",
    "Manufacturer PostalCode",
    "Manufacturer Country",
]
