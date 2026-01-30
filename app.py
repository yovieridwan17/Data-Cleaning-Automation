from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import os
import uuid
from io import BytesIO

app = Flask(__name__, template_folder='templates', static_folder='static')
DATA = {}  # store DataFrames in-memory for the session (simple approach for local use)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXT = ['.csv', '.xls', '.xlsx']

def read_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        return pd.read_csv(path)
    else:
        return pd.read_excel(path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return render_template('index.html', error='No file uploaded')
        filename = f.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXT:
            return render_template('index.html', error='Unsupported file type')
        uid = uuid.uuid4().hex
        save_path = os.path.join(UPLOAD_FOLDER, uid + ext)
        f.save(save_path)
        df = read_file(save_path)
        DATA[uid] = df
        return redirect(url_for('edit', uid=uid))
    return render_template('index.html')

@app.route('/edit/<uid>', methods=['GET'])
def edit(uid):
    df = DATA.get(uid)
    if df is None:
        return redirect(url_for('index'))
    info = {
        'rows': len(df),
        'cols': len(df.columns),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing': df.isnull().sum().to_dict(),
        'duplicates': int(df.duplicated().sum())
    }
    head_html = df.head().to_html(classes='table', index=False)
    return render_template('edit.html', uid=uid, info=info, head_html=head_html, columns=list(df.columns))

@app.route('/apply/<uid>', methods=['POST'])
def apply(uid):
    df = DATA.get(uid)
    if df is None:
        return redirect(url_for('index'))
    action = request.form.get('action')
    col = request.form.get('column')
    # perform actions
    if action == 'dropna':
        df = df.dropna()
    elif action == 'fill_value':
        val = request.form.get('value')
        if col:
            df[col] = df[col].fillna(val)
    elif action == 'ffill':
        if col:
            df[col] = df[col].fillna(method='ffill')
    elif action == 'bfill':
        if col:
            df[col] = df[col].fillna(method='bfill')
    elif action == 'median':
        if col and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
    elif action == 'mode':
        if col:
            m = df[col].mode()
            if not m.empty:
                df[col] = df[col].fillna(m[0])
    elif action == 'mean':
        if col and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())
    elif action == 'drop_duplicates':
        subset = request.form.get('dup_subset')
        if subset:
            cols = [c.strip() for c in subset.split(',') if c.strip() in df.columns]
            df = df.drop_duplicates(subset=cols if cols else None)
        else:
            df = df.drop_duplicates()
    elif action == 'drop_column':
        if col and col in df.columns:
            df = df.drop(columns=[col])
    elif action == 'add_column':
        new_col = request.form.get('value')
        if new_col and new_col not in df.columns:
            df[new_col] = ''
    elif action == 'calc_column':
        op = request.form.get('calc_op')
        col1 = request.form.get('calc_col1')
        col2 = request.form.get('calc_col2')
        new_col = request.form.get('new') or 'hasil'
        if op in ['add','sub','mul','div'] and col1 and col2 and col1 in df.columns and col2 in df.columns:
            if op == 'add':
                df[new_col] = df[col1] + df[col2]
            elif op == 'sub':
                df[new_col] = df[col1] - df[col2]
            elif op == 'mul':
                df[new_col] = df[col1] * df[col2]
            elif op == 'div':
                df[new_col] = df[col1] / df[col2]
        elif op == 'single' and col1 and col1 in df.columns:
            single_op = request.form.get('calc_single_op')
            if single_op == 'percent':
                df[new_col] = df[col1] / 100
            elif single_op == 'neg':
                df[new_col] = -df[col1]
            elif single_op == 'square':
                df[new_col] = df[col1] ** 2
            elif single_op == 'sqrt':
                df[new_col] = df[col1] ** 0.5
            elif single_op == 'log':
                import numpy as np
                df[new_col] = df[col1].apply(lambda x: np.log(x) if x > 0 else None)
            elif single_op == 'custom':
                exp = request.form.get('calc_single_exp')
                if exp:
                    try:
                        df[new_col] = df[col1].apply(lambda x: eval(exp, {}, {'x': x}))
                    except Exception:
                        pass
    elif action == 'replace':
        old = request.form.get('old')
        new = request.form.get('new')
        if col and old is not None:
            df[col] = df[col].replace(old, new)
    elif action == 'normalize_lower':
        if col:
            df[col] = df[col].astype(str).str.lower()
    elif action == 'normalize_strip':
        if col:
            df[col] = df[col].astype(str).str.strip()
    elif action == 'normalize_clean':
        if col:
            import re
            df[col] = df[col].astype(str).apply(lambda x: re.sub(r"[^a-zA-Z\s]", "", x))
    elif action == 'astype':
        typ = request.form.get('to_type')
        if col and typ:
            try:
                if typ == 'str':
                    df[col] = df[col].astype(str)
                elif typ == 'int':
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                elif typ == 'float':
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
                elif typ == 'datetime':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass
    elif action == 'outlier_iqr':
        if col and pd.api.types.is_numeric_dtype(df[col]):
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            low = q1 - 1.5 * iqr
            high = q3 + 1.5 * iqr
            df = df[(df[col] >= low) & (df[col] <= high)]
    # save back
    DATA[uid] = df
    return redirect(url_for('edit', uid=uid))

@app.route('/download/<uid>', methods=['GET'])
def download(uid):
    df = DATA.get(uid)
    if df is None:
        return redirect(url_for('index'))
    fmt = request.args.get('fmt', 'csv')
    filename = request.args.get('filename') or f'cleaned_{uid}.{fmt}'
    out_path = os.path.join(OUTPUT_FOLDER, filename)
    if fmt == 'csv':
        df.to_csv(out_path, index=False)
    else:
        df.to_excel(out_path, index=False)
    return send_file(out_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=8501)
