"""
PDF Invoice Generation using ReportLab
Produces clean, print-ready A4 GST/POS invoices with accurate tax and discount breakdowns.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from models import Setting


def get_setting(key: str, default_value: str = "") -> str:
    """Retrieve a setting value from the database with fallback."""
    setting = Setting.query.filter_by(key=key).first()
    if setting and setting.value is not None:
        return setting.value
    return default_value


def generate_invoice_pdf(order) -> BytesIO:
    """Generate a formatted A4 PDF invoice for an Order."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {order.invoice_number}",
    )

    shop_name = get_setting("shop_name", "Trio Snacks")
    shop_address = get_setting("shop_address", "123 Main Street, City")
    shop_phone = get_setting("shop_phone", "+91 9876543210")
    footer_text = get_setting("invoice_footer", "Thank you for visiting Trio Snacks!")

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ShopTitle",
        parent=styles["Heading1"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#111827"),
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ShopSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )

    # Header Banner
    elements.append(Paragraph(shop_name.upper(), title_style))
    elements.append(Paragraph("HEAVEN OF DELICIOUS • FRESH SNACKS & BEVERAGES", subtitle_style))
    if shop_address:
        elements.append(Paragraph(shop_address, subtitle_style))
    if shop_phone:
        elements.append(Paragraph(f"Phone: {shop_phone}", subtitle_style))

    elements.append(Spacer(1, 6 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#F59E0B")))
    elements.append(Spacer(1, 5 * mm))

    # Invoice & Customer Metadata Table
    customer_name = order.customer_name.strip() if order.customer_name else "Walk-in Customer"
    customer_phone = order.customer_phone.strip() if order.customer_phone else "-"
    cashier_name = order.user.username.title() if getattr(order, "user", None) else "Staff"

    meta_data = [
        ["Invoice Number:", order.invoice_number, "Customer:", customer_name],
        [
            "Date & Time:",
            order.created_at.strftime("%d %b %Y, %I:%M %p"),
            "Phone:",
            customer_phone,
        ],
        ["Billed By:", cashier_name, "Status:", "PAID"],
    ]

    meta_table = Table(meta_data, colWidths=[32 * mm, 60 * mm, 28 * mm, 54 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    # Line Items Table
    elements.append(Paragraph("Order Summary", section_heading))

    items_data = [["#", "Item Description", "Qty", "Unit Price (Rs.)", "Total (Rs.)"]]
    for idx, item in enumerate(order.items, 1):
        item_name = item.product.name if item.product else f"Item #{item.product_id}"
        items_data.append(
            [
                str(idx),
                item_name,
                str(item.quantity),
                f"Rs. {item.unit_price:.2f}",
                f"Rs. {item.total_price:.2f}",
            ]
        )

    items_table = Table(
        items_data, colWidths=[14 * mm, 82 * mm, 20 * mm, 30 * mm, 28 * mm]
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FBBF24")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#FFFBEB")],
                ),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 5 * mm))

    # Totals Breakdown (Consistent with Order record)
    totals_data = [
        ["Subtotal:", f"Rs. {order.subtotal:.2f}"],
    ]
    if order.tax_amount and order.tax_amount > 0:
        totals_data.append(["Tax / GST:", f"+ Rs. {order.tax_amount:.2f}"])
    if order.discount_amount and order.discount_amount > 0:
        totals_data.append(["Discount:", f"- Rs. {order.discount_amount:.2f}"])
    totals_data.append(["Grand Total:", f"Rs. {order.total_amount:.2f}"])

    totals_table = Table(totals_data, colWidths=[130 * mm, 44 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -2), 10),
                ("FONTSIZE", (0, -1), (-1, -1), 12),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#F59E0B")),
            ]
        )
    )
    elements.append(totals_table)
    elements.append(Spacer(1, 12 * mm))

    # Footer
    footer_style = ParagraphStyle(
        "InvoiceFooter",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6B7280"),
    )
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
