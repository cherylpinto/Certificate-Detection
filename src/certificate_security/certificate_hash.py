'''
1. This file is part of Certificate Cipher Tool.
2. It provides functionalities to encrypt and decrypt JSON data and images using password-based encryption.
3. It also includes a feature to add a watermark to decrypted images.

Functions name : 
    - derive_key()
    - encrypt()
    - decrypt()
    - print_table()
    - encrypt_image()
    - decrypt_image()
    - add_watermark()
'''

from cryptography.fernet import Fernet
import base64
import os
import json
import io
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich.console import Console
from rich.table import Table
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.logging import get_logger

console = Console()
logger = get_logger("Certificate Cipher Tool")

class CertificateCipher:
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a secret key from the password and salt using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    # ---------------- JSON / Dict Encryption ----------------
    def encrypt(self, data: dict, password: str) -> str:
        plain_text = json.dumps(data)
        salt = os.urandom(16)
        key = self.derive_key(password, salt)
        f = Fernet(key)
        cipher_text = f.encrypt(plain_text.encode())
        logger.info("Data encrypted successfully.")
        return base64.urlsafe_b64encode(salt + cipher_text).decode()

    def decrypt(self, cipher_text: str, password: str) -> dict:
        data = base64.urlsafe_b64decode(cipher_text.encode())
        salt, ct = data[:16], data[16:]
        key = self.derive_key(password, salt)
        f = Fernet(key)
        plain_text = f.decrypt(ct).decode()
        logger.info("Data decrypted successfully.")
        return json.loads(plain_text)

    def print_table(self, data: dict):
        table = Table(title="Decrypted Certificate Data")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        for key, value in data.items():
            table.add_row(key, str(value))
        console.print(table)

    # ---------------- Image Encryption ----------------
    def encrypt_image(self, image_bytes: bytes, password: str) -> str:
        salt = os.urandom(16)
        key = self.derive_key(password, salt)
        f = Fernet(key)
        cipher_bytes = f.encrypt(image_bytes)
        logger.info("Image encrypted successfully.")
        return base64.urlsafe_b64encode(salt + cipher_bytes).decode()

    def decrypt_image(self, cipher_text: str, password: str) -> Image.Image:
        data = base64.urlsafe_b64decode(cipher_text.encode())
        salt, ct = data[:16], data[16:]
        key = self.derive_key(password, salt)
        f = Fernet(key)
        decrypted_bytes = f.decrypt(ct)
        image = Image.open(io.BytesIO(decrypted_bytes))
        logger.info("Image decrypted successfully.")
        return image

    # ---------------- Add Watermark ----------------
    def add_watermark(self, image: Image.Image, watermark_text: str = "VERIFIED") -> Image.Image:
        # Convert image to RGBA
        image = image.convert("RGBA")
        
        # Create a transparent layer same size as image
        txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Large font: scale based on image diagonal
        diagonal = int((image.width**2 + image.height**2) ** 0.5)
        font_size = int(diagonal * 0.09)  # 15% of diagonal
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Position in center of image
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2

        # Draw rotated watermark directly on txt_layer
        temp = Image.new("RGBA", image.size, (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp)
        temp_draw.text((x, y), watermark_text, font=font, fill=(202, 206, 207, 255))
        rotated = temp.rotate(45, expand=False)
        
        # Merge watermark with original image
        watermarked = Image.alpha_composite(image, rotated)
        logger.info("Watermark added to image successfully.")
        return watermarked.convert("RGB")


if __name__ == "__main__":
    # Sample certificate data
    certificate_data = {
        "certificate_id": "34254435435",
        "name": "Praveen",
        "dob": "10-10-2000",
        "college": "KMEC",
        "university": "VTU",
        "course": "CSE",
        "year_of_passing": "2024",
        "gpa": "9.2",
        "roll_no": "1MS19CS001",
        "issued_on": "01-01-2024"
    }

    # Sample password
    password = "SamplePassword123!"

    # Initialize cipher tool
    cert_tool = CertificateCipher()

    # ---------------- Encrypt & Decrypt JSON ----------------
    cipher_text = cert_tool.encrypt(certificate_data, password)
    console.print("\n[cyan]Encrypted (Cipher Text for JSON):[/cyan]")
    print(cipher_text)

    try:
        decrypted_data = cert_tool.decrypt(cipher_text, password)
        console.print("\n[green]Decrypted JSON Data in Table Format:[/green]\n")
        cert_tool.print_table(decrypted_data)
    except Exception as e:
        console.print(f"[red]Decryption failed: {e}[/red]")

    # ---------------- Encrypt & Decrypt Image ----------------
    try:
        # Load sample image (replace with user input bytes in real scenario)
        with open("./data/sample.jpg", "rb") as f:
            image_bytes = f.read()

        encrypted_image = cert_tool.encrypt_image(image_bytes, password)
        console.print("\n[cyan]Encrypted Image Cipher Text:[/cyan]")
        print(encrypted_image[:100] + "...")  # print only first 100 chars

        decrypted_image = cert_tool.decrypt_image(encrypted_image, password)
        watermarked_image = cert_tool.add_watermark(decrypted_image)

        # Show image
        watermarked_image.save("./outputs/decrypted_watermarked.png")
        watermarked_image.show()
        console.print("[green]Image decrypted and watermarked successfully![/green]")

    except FileNotFoundError:
        console.print("[red]Sample image file not found! Place a 'sample_certificate.png' in the directory.[/red]")
    except Exception as e:
        console.print(f"[red]Image encryption/decryption failed: {e}[/red]")

print("\nThank you for using the Certificate Cipher Tool!")
