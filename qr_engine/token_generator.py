import qrcode

def generate_qr(token_qr):
    """
    Generate QR dari token backend
    """
    filename = f"qr_{token_qr[:8]}.png"
    
    img = qrcode.make(token_qr)
    img.save(filename)

    print(f"QR berhasil dibuat: {filename}")
    
    return filename