import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import PyKCS11
from datetime import datetime
import fitz  # PyMuPDF for PDF preview
import re   # Regular expressions for pattern matching

# Function to create a signature appearance with token username and timestamp
def create_signature_appearance(username, timestamp):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Define rectangle dimensions and draw it
    rect_x = 100
    rect_y = 100
    rect_width = 300
    rect_height = 100
    can.rect(rect_x, rect_y, rect_width, rect_height, stroke=1, fill=0)  # x, y, width, height

    # Add text inside the rectangle
    text_x = rect_x + 20
    text_y = rect_y + 70
    can.drawString(text_x, text_y, f"Digitally Signed by: {username}")
    can.drawString(text_x, text_y - 20, f"Timestamp: {timestamp}")

    can.save()
    packet.seek(0)
    return PdfReader(packet)

# Function to access the digital signature from the token
def access_token_signature(pkcs11_lib_path, pin):
    print("Accessing token signature...")
    try:
        pkcs11 = PyKCS11.PyKCS11Lib()
        pkcs11.load(pkcs11_lib_path)

        slots = pkcs11.getSlotList()
        session = pkcs11.openSession(slots[0])
        session.login(pin)

        # Assuming the token has a certificate object
        certs = session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)])
        cert = certs[0]

        # Retrieve username (label) from the token's certificate
        token_info = session.getAttributeValue(cert, [PyKCS11.CKA_LABEL])[0]

        # Check the type of token_info
        if isinstance(token_info, bytes):
            username = token_info.decode('utf-8')
        else:
            username = str(token_info)  # Convert to string if it's not bytes

        # Example: Generate a timestamp for the signature
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        session.logout()
        session.closeSession()

        print(f"Token username (CKA_LABEL): {username}")
        print(f"Timestamp: {timestamp}")
        print("Token signature accessed.")
        return cert, username, timestamp  # Return cert, username, and timestamp
    except PyKCS11.PyKCS11Error as e:
        print(f"PyKCS11Error: {e}")
    except Exception as e:
        print(f"Exception occurred while accessing token: {e}")

    return None, None, None  # Return None values if there's an error

# Function to sign a PDF using the digital signature from the token
def sign_pdf(input_pdf_path, output_pdf_path, pkcs11_lib_path, pin):
    print(f"Signing PDF: {input_pdf_path}")
    existing_pdf = PdfReader(open(input_pdf_path, "rb"))
    output = PdfWriter()

    # Access the certificate, username, and timestamp from the token
    print("Accessing token for signature...")
    cert, username, timestamp = access_token_signature(pkcs11_lib_path, pin)

    if cert and username and timestamp:
        # Create a signature appearance
        print("Creating signature appearance...")
        signature_appearance = create_signature_appearance(username, timestamp)

        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            if i == 0:  # Add the signature to the first page
                page.merge_page(signature_appearance.pages[0])
            output.add_page(page)

        # Save the signed PDF
        print(f"Saving signed PDF to: {output_pdf_path}")
        try:
            with open(output_pdf_path, "wb") as outputStream:
                output.write(outputStream)
            print("PDF signing complete.")
        except Exception as e:
            print(f"Error saving signed PDF: {e}")
    else:
        print("Failed to access token or retrieve signature details.")

# Function to find occurrences of a word in a PDF using PyMuPDF (fitz)
def find_word_in_pdf(pdf_path, word):
    occurrences = []

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Iterate through each page of the PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)

        # Extract text from the page
        text = page.get_text()

        # Find all occurrences of the word in the text of the page
        page_occurrences = [(match.start(), match.end()) for match in re.finditer(r'\b{}\b'.format(re.escape(word)), text)]
        if page_occurrences:
            occurrences.extend([(page_num + 1, start, end) for start, end in page_occurrences])

    pdf_document.close()

    return occurrences

# Function to draw rectangle around word and sign PDF
def draw_and_sign_pdf(input_pdf_path, output_pdf_path, pkcs11_lib_path, pin, word_coordinates, username, timestamp):
    # Open the original PDF
    pdf_document = fitz.open(input_pdf_path)

    for page_num, start, end in word_coordinates:
        page = pdf_document.load_page(page_num - 1)
        word_text = page.get_text()[start:end]

        # Get the first rectangle of the first occurrence of the found word
        rect = page.search_for(word_text)[0]

        # Create a signature appearance
        signature_appearance = create_signature_appearance(username, timestamp)

        # Add redacted annotation around the found word
        annot = page.add_redact_annot(rect)

        # Calculate the position for the text box
        text_x = rect.x0 + 10  # Adjust x position as needed
        text_y = rect.y0 - 30  # Adjust y position as needed

        # Add text box with signature information
        page.insert_textbox((text_x, text_y), f"Digitally Signed by: {username}\nTimestamp: {timestamp}", fontsize=10)

    # Save the signed PDF
    pdf_document.save(output_pdf_path)
    pdf_document.close()

    print(f"PDF signed with rectangle around word and signature added.")

    print(f"PDF signed with rectangle around word and signature added.")


    print(f"PDF signed with rectangle around word and signature added.")

    print(f"PDF signed with rectangle around word and signature added.")


    print(f"PDF signed with rectangle around word and signature added.")

# Paths to files and PKCS#11 library
input_pdf_path = r"C:\Users\saravanan\Downloads\sample1.pdf"
output_pdf_path = r"C:\Users\saravanan\projects\signed.pdf"
pkcs11_lib_path = r"C:\Windows\System32\eps2003csp11.dll"  # Adjust to your PKCS#11 library path
pin = "12345678"  # Your PIN
word_to_find = "AUTHORISED SIGNATORY"

# Find occurrences of the word in the original PDF
word_coordinates = find_word_in_pdf(input_pdf_path, word_to_find)

if word_coordinates:
    print(f'Word "{word_to_find}" found in the original PDF.')

    # Access the certificate, username, and timestamp from the token
    print("Accessing token for signature...")
    cert, username, timestamp = access_token_signature(pkcs11_lib_path, pin)

    # Draw rectangle around word and sign the PDF
    draw_and_sign_pdf(input_pdf_path, output_pdf_path, pkcs11_lib_path, pin, word_coordinates, username, timestamp)

    print(f'PDF signed with rectangle around word "{word_to_find}".')
else:
    print(f'Word "{word_to_find}" not found in the original PDF.')
