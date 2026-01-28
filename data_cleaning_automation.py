import pandas as pd
import os

# Step 1: Import Data
def import_data():
    print('Pilih file data yang ingin di-cleaning:')
    file_path = input('Masukkan path file (misal: data.csv): ')
    if not os.path.exists(file_path):
        print('File tidak ditemukan!')
        return None
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
    else:
        print('Ekstensi file tidak didukung!')
        return None
    print(f'Berhasil mengimpor data dengan {len(df)} baris dan {len(df.columns)} kolom.')
    return df, file_path

# Step 2: Pilih Kolom
def pilih_kolom(df):
    print('Kolom yang tersedia:')
    for i, col in enumerate(df.columns):
        print(f'{i+1}. {col}')
    idx = int(input('Pilih nomor kolom yang ingin dicek typo: ')) - 1
    if idx < 0 or idx >= len(df.columns):
        print('Pilihan tidak valid!')
        return None
    return df.columns[idx]

# Step 3: Cek Typo dan Perbaiki
def perbaiki_typo(df, kolom):
    unique_vals = df[kolom].astype(str).unique()
    print(f'Nilai unik pada kolom {kolom}:')
    for i, val in enumerate(unique_vals):
        print(f'{i+1}. {val}')
    idx = int(input('Pilih nomor kata yang ingin diperbaiki (0 untuk selesai): ')) - 1
    while idx >= 0 and idx < len(unique_vals):
        kata_salah = unique_vals[idx]
        kata_benar = input(f'Masukkan kata pengganti untuk "{kata_salah}": ')
        df[kolom] = df[kolom].replace(kata_salah, kata_benar)
        print(f'Kata "{kata_salah}" telah diganti menjadi "{kata_benar}".')
        unique_vals = df[kolom].astype(str).unique()
        for i, val in enumerate(unique_vals):
            print(f'{i+1}. {val}')
        idx = int(input('Pilih nomor kata yang ingin diperbaiki (0 untuk selesai): ')) - 1
    return df

def hapus_missing(df):
    print('1. Hapus baris dengan data kosong')
    print('2. Isi data kosong dengan nilai tertentu')
    print('3. Forward fill (isi dengan nilai sebelumnya)')
    print('4. Backward fill (isi dengan nilai setelahnya)')
    print('5. Isi dengan median (kolom numerik)')
    print('6. Isi dengan modus (mode)')
    print('7. Isi dengan rata-rata (mean, kolom numerik)')
    pilihan = input('Pilih opsi (1-7, 0 untuk batal): ')
    if pilihan == '1':
        df = df.dropna()
        print('Baris dengan data kosong telah dihapus.')
    elif pilihan == '2':
        kolom = pilih_kolom(df)
        if kolom:
            nilai = input(f'Masukkan nilai pengganti untuk data kosong di kolom {kolom}: ')
            df[kolom] = df[kolom].fillna(nilai)
            print(f'Data kosong di kolom {kolom} telah diisi dengan "{nilai}".')
    elif pilihan == '3':
        kolom = pilih_kolom(df)
        if kolom:
            df[kolom] = df[kolom].fillna(method='ffill')
            print(f'Data kosong di kolom {kolom} telah diisi dengan forward fill.')
    elif pilihan == '4':
        kolom = pilih_kolom(df)
        if kolom:
            df[kolom] = df[kolom].fillna(method='bfill')
            print(f'Data kosong di kolom {kolom} telah diisi dengan backward fill.')
    elif pilihan == '5':
        kolom = pilih_kolom(df)
        if kolom and pd.api.types.is_numeric_dtype(df[kolom]):
            median = df[kolom].median()
            df[kolom] = df[kolom].fillna(median)
            print(f'Data kosong di kolom {kolom} telah diisi dengan median ({median}).')
        else:
            print('Kolom tidak numerik.')
    elif pilihan == '6':
        kolom = pilih_kolom(df)
        if kolom:
            mode = df[kolom].mode()
            if not mode.empty:
                df[kolom] = df[kolom].fillna(mode[0])
                print(f'Data kosong di kolom {kolom} telah diisi dengan modus ({mode[0]}).')
            else:
                print('Tidak ditemukan modus.')
    elif pilihan == '7':
        kolom = pilih_kolom(df)
        if kolom and pd.api.types.is_numeric_dtype(df[kolom]):
            mean = df[kolom].mean()
            df[kolom] = df[kolom].fillna(mean)
            print(f'Data kosong di kolom {kolom} telah diisi dengan rata-rata ({mean}).')
        else:
            print('Kolom tidak numerik.')
    return df

def hapus_duplikat(df):
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    print(f'{before-after} baris duplikat telah dihapus.')
    return df

def ubah_tipe_data(df):
    kolom = pilih_kolom(df)
    if kolom:
        print('Tipe data saat ini:', df[kolom].dtype)
        print('Pilih tipe data baru:')
        print('1. String')
        print('2. Integer')
        print('3. Float')
        tipe = input('Pilihan (1/2/3): ')
        try:
            if tipe == '1':
                df[kolom] = df[kolom].astype(str)
            elif tipe == '2':
                df[kolom] = pd.to_numeric(df[kolom], errors='coerce').astype('Int64')
            elif tipe == '3':
                df[kolom] = pd.to_numeric(df[kolom], errors='coerce').astype(float)
            print(f'Tipe data kolom {kolom} telah diubah.')
        except Exception as e:
            print('Gagal mengubah tipe data:', e)
    return df

def normalisasi_teks(df):
    kolom = pilih_kolom(df)
    if kolom:
        print('1. Ubah ke lowercase')
        print('2. Strip whitespace')
        print('3. Hapus karakter non-alfabet')
        pilihan = input('Pilih aksi (1/2/3, 0 untuk batal): ')
        if pilihan == '1':
            df[kolom] = df[kolom].astype(str).str.lower()
            print(f'Kolom {kolom} telah diubah ke lowercase.')
        elif pilihan == '2':
            df[kolom] = df[kolom].astype(str).str.strip()
            print(f'Whitespace di kolom {kolom} telah dihapus.')
        elif pilihan == '3':
            import re
            df[kolom] = df[kolom].astype(str).apply(lambda x: re.sub(r"[^a-zA-Z\s]", "", x))
            print(f'Karakter non-alfabet di kolom {kolom} telah dihapus.')
    return df

# Step 4: Simpan Data
def simpan_data(df, file_path):
    ext = os.path.splitext(file_path)[1].lower()
    out_path = input('Masukkan nama file output lengkap beserta ekstensi (misal: hasil_cleaning.csv atau hasil.xlsx): ')
    if out_path.endswith('.csv'):
        df.to_csv(out_path, index=False)
    elif out_path.endswith('.xls') or out_path.endswith('.xlsx'):
        df.to_excel(out_path, index=False)
    else:
        print('Ekstensi file output tidak didukung. Data tidak disimpan.')
        return
    print(f'Data bersih telah disimpan ke {out_path}')

# Menu utama cleaning
def menu_cleaning(df):
    while True:
        print('\n=== MENU DATA CLEANING ===')
        print('1. Cek & perbaiki typo')
        print('2. Hapus/isi data kosong')
        print('3. Hapus duplikat')
        print('4. Ubah tipe data kolom')
        print('5. Normalisasi teks')
        print('0. Selesai & simpan')
        pilihan = input('Pilih aksi: ')
        if pilihan == '1':
            kolom = pilih_kolom(df)
            if kolom:
                df = perbaiki_typo(df, kolom)
        elif pilihan == '2':
            df = hapus_missing(df)
        elif pilihan == '3':
            df = hapus_duplikat(df)
        elif pilihan == '4':
            df = ubah_tipe_data(df)
        elif pilihan == '5':
            df = normalisasi_teks(df)
        elif pilihan == '0':
            break
        else:
            print('Pilihan tidak valid!')
    return df

if __name__ == '__main__':
    df, file_path = import_data()
    if df is not None:
        df = menu_cleaning(df)
        simpan_data(df, file_path)
