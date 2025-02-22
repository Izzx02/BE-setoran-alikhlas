from flask import Flask, render_template, request, redirect, send_file
import pymysql
import openpyxl
from datetime import datetime
import os

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/assets')

# Koneksi ke database
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="setoran_alikhlas",
    cursorclass=pymysql.cursors.DictCursor  # ✅ Gunakan DictCursor
)

@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama FROM santri")
    daftar_santri = cursor.fetchall()
    return render_template('index.html', daftar_santri=daftar_santri)

@app.route('/submit_setoran', methods=['POST'])
def submit_setoran():
    santri_id = request.form['santri_id']
    jumlah_sholawat = request.form['jumlah_sholawat']
    
    cursor = conn.cursor()
    
    # Hapus setoran lama jika sudah ada
    cursor.execute(
        "DELETE FROM setoran WHERE santri_id = %s AND tanggal = CURDATE()", (santri_id,)
    )

    # Tambahkan setoran baru
    cursor.execute(
        "INSERT INTO setoran (santri_id, tanggal, jumlah_sholawat) VALUES (%s, CURDATE(), %s)",
        (santri_id, jumlah_sholawat)
    )

    conn.commit()
    return redirect('/')

@app.route('/download_excel')
def download_excel():
    password = request.args.get("pw")  # Ambil password dari URL
    if password != "izza":  # Ganti dengan password kamu
        return "Akses Ditolak!", 403  

    conn.commit()  # Pastikan perubahan terbaru disimpan sebelum mengambil data

    cursor = conn.cursor()
    cursor.execute("""
    SELECT santri.nama, IFNULL(setoran.jumlah_sholawat, 0) AS jumlah_sholawat
    FROM santri
    LEFT JOIN setoran ON santri.id = setoran.santri_id
    ORDER BY santri.id
""")

    data = cursor.fetchall()

    # Buat folder 'temp' jika belum ada
    if not os.path.exists("temp"):
        os.makedirs("temp")

    # Buat file Excel dengan openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nama", "Jumlah Sholawat"])  # Header

    for row in data:
        ws.append([row['nama'], row['jumlah_sholawat']])

    # Simpan di folder 'temp'
    filename = f"temp/setoran_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    wb.save(filename)  

    # Pastikan Flask bisa menemukan file dengan path absolut
    filepath = os.path.abspath(filename)

    response = send_file(filepath, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Hapus file setelah dikirim agar tidak menumpuk
    os.remove(filepath)

    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
