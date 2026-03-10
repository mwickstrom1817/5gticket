import qrcode
import qrcode.image.svg
import io
import base64


PORTAL_URL = "https://5gticket.streamlit.app"


def generate_qr_base64(equipment_id: int) -> str:
    """Generate a QR code for an equipment item and return as base64 PNG."""
    url = f"{PORTAL_URL}?equipment_id={equipment_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()


def generate_qr_bytes(equipment_id: int) -> bytes:
    """Generate a QR code and return as raw PNG bytes for download."""
    url = f"{PORTAL_URL}?equipment_id={equipment_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.read()
