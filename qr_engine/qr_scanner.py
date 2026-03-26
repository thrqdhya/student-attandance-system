from pyzbar.pyzbar import decode
from PIL import Image

def scan_qr(qr_file):
    """
    Scan QR dari file
    """
    img = Image.open(qr_file)
    result = decode(img)

    if result:
        token = result[0].data.decode()
        print("Hasil scan:", token)
        return token
    else:
        print("QR tidak terbaca")
        return None