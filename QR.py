import qrcode
import datetime
import pandas as pd
import mysql.connector
import uuid

# Database simulasi untuk menyimpan status pemindaian
scanned_qr_codes = set()

def create_qr_code_with_timestamp(data, unique_id):
    # Generate current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Combine data with timestamp and unique ID
    data_with_timestamp = f"{data}\nScanned at: {timestamp}\nID: {unique_id}"
    return data_with_timestamp

def insert_data_to_database(data_frame):
    try:
        # Membuat koneksi ke database MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="qrcode"
        )

        # Membuat kursor
        cursor = conn.cursor()

        # Mengekstrak data dari DataFrame pandas ke dalam database
        for index, row in data_frame.iterrows():
            query = "INSERT INTO peserta (NISN, Nama, telepon, email) VALUES (%s, %s, %s, %s)"
            values = (row['nisn'], row['nama'], row['tel'], row['email'])

            # Eksekusi query INSERT
            cursor.execute(query, values)

        # Commit perubahan dan menutup kursor dan koneksi
        conn.commit()
        cursor.close()
        conn.close()

        print("Data berhasil dimasukkan ke dalam database.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def created_v_card(nama, tell, email, scanned=False):
    scanned_info = "Scanned: Yes" if scanned else "Scanned: No"
    vcard = f"BEGIN:VCARD\n"\
            f"VERSION:3.0\n"\
            f"FN:{nama}\n"\
            f"TEL:{tell}\n"\
            f"EMAIL:{email}\n"\
            f"STATUS:{scanned_info}\n"\
            f"END:VCARD"
    return vcard
def save_to_database(NISN, nama, tell, email, unique_id, scanned):
    try:
        # Membuat koneksi ke database MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="qrcode"
        )

        # Membuat kursor
        cursor = conn.cursor()

        # Mengecek apakah tabel qrcode sudah ada, jika belum, maka dibuat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qrcode (
                id INT AUTO_INCREMENT PRIMARY KEY,
                NISN VARCHAR(255),
                Nama VARCHAR(255),
                telepon VARCHAR(255),
                email VARCHAR(255),
                unique_id VARCHAR(255),
                scanned BOOLEAN DEFAULT FALSE,
                date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Mengecek apakah QR code sudah pernah discan sebelumnya
        cursor.execute('SELECT scanned FROM qrcode WHERE unique_id = %s', (str(unique_id),))
        result = cursor.fetchone()

        # Jika QR code sudah pernah discan, tampilkan pesan
        if result and result[0]:
            print(f"QR code with ID {unique_id} has already been scanned.")
        else:
            # Memasukkan data ke tabel qrcode dengan nilai scanned yang diterima dari argumen
            cursor.execute('''
                INSERT INTO qrcode (NISN, Nama, telepon, email, unique_id, scanned)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (NISN, nama, tell, email, str(unique_id), scanned))

            # Commit perubahan
            conn.commit()
            print(f"Data for QR code with ID {unique_id} has been inserted into the database.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Menutup koneksi
        cursor.close()
        conn.close()


def mark_as_scanned(unique_id):
    try:
        # Membuat koneksi ke database MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="qrcode"
        )

        cursor = conn.cursor()

        # Mengecek apakah QR code dengan unique_id sudah pernah discan sebelumnya
        cursor.execute('SELECT scanned FROM qrcode WHERE unique_id = %s', (str(unique_id),))
        result = cursor.fetchone()

        # Jika QR code belum pernah discan, update nilai scanned menjadi TRUE
        if result[0]:
            cursor.execute('''
                UPDATE qrcode
                SET scanned = 1
                WHERE unique_id = %s
            ''', (str(unique_id),1))

            # Commit perubahan dan menutup koneksi
            conn.commit()
            print(f"QR code with ID {unique_id} has been marked as scanned.")
        else:
            print(f"QR code with ID {unique_id} has already been scanned.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Menutup koneksi
        if conn.is_connected():
            cursor.close()
            conn.close()
if __name__ == "__main__":
    # Load data from the CSV file
    csv = "osis.csv"
    df = pd.read_csv(csv)

    # Insert data into the database using insert_data_to_database function
    insert_data_to_database(df)

    # Data to be encoded in the QR code
    data_to_encode = "hallo selamat datang di Pensi 2024."

    for index, row in df.iterrows():
        # Extract data from the DataFrame
        NISN = row['nisn']
        nama = row['nama']
        tell = row['tel']
        email = row['email']

        # Unique ID for each QR code
        unique_id = str(uuid.uuid4())

        # Check if QR code has been scanned before
        if unique_id in scanned_qr_codes:
            print(f"QR code with ID {unique_id} has already been scanned.")
            continue

        # Create QR code with timestamp and unique ID
        data_with_timestamp = create_qr_code_with_timestamp(data_to_encode, unique_id)

        # Create vCard
        vcard_data = created_v_card(nama, tell, email, scanned=False)

        # Combine data and vCard
        combine_data = f"{data_with_timestamp}\n{vcard_data}"

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(combine_data)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        img = qr.make_image(fill_color="white", back_color="black")

        # Save or display the QR code image with unique names
        img.save(f"qr_code_{unique_id}.png", "PNG")

        # Save to database with scanned=False (assuming the QR code has not been scanned yet)
        save_to_database(NISN, nama, tell, email, unique_id, scanned=True)

        # Mark QR code as scanned
        scanned_qr_codes.add(unique_id)
