"""
============================================
IDS ESP32 - Server Python Sederhana
============================================
Menerima log serangan dari ESP32
dan menampilkan di dashboard web

Kebutuhan:
    pip install flask

Cara jalankan:
    python server.py

Lalu buka browser: http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json

app = Flask(__name__)

# Simpan log di memory (sederhana, tidak perlu database dulu)
log_serangan = []

# ============================================
# TEMPLATE DASHBOARD HTML
# ============================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="5">
  <title>IDS ESP32 - Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; padding: 24px; }
    h1 { font-size: 22px; margin-bottom: 4px; color: #ffffff; }
    .subtitle { font-size: 13px; color: #888; margin-bottom: 24px; }

    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .stat { background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 10px; padding: 16px 20px; }
    .stat-label { font-size: 12px; color: #888; margin-bottom: 6px; }
    .stat-val { font-size: 28px; font-weight: 600; color: #fff; }
    .stat-val.merah { color: #ff5c5c; }
    .stat-val.hijau { color: #4caf82; }
    .stat-val.kuning { color: #f0b429; }

    h2 { font-size: 15px; margin-bottom: 12px; color: #ccc; }
    table { width: 100%; border-collapse: collapse; background: #1a1d27; border-radius: 10px; overflow: hidden; }
    th { background: #22263a; padding: 10px 14px; text-align: left; font-size: 12px; color: #888; font-weight: 500; }
    td { padding: 10px 14px; font-size: 13px; border-top: 1px solid #2a2d3a; }
    tr:hover td { background: #1f2235; }

    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
    .badge-http   { background: #1a3a5c; color: #5bc0eb; }
    .badge-mqtt   { background: #1a3a2a; color: #4caf82; }
    .badge-telnet { background: #3a1a1a; color: #ff5c5c; }

    .empty { text-align: center; padding: 40px; color: #555; font-size: 14px; }
    .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #4caf82; margin-right: 6px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
    .live-badge { font-size: 12px; color: #4caf82; display: flex; align-items: center; }
  </style>
</head>
<body>
  <div class="header-row">
    <div>
      <h1>🛡 IDS ESP32 — Dashboard</h1>
      <p class="subtitle">Monitoring serangan real-time • Auto-refresh setiap 5 detik</p>
    </div>
    <div class="live-badge">
      <span class="status-dot"></span> LIVE
    </div>
  </div>

  <div class="stats">
    <div class="stat">
      <div class="stat-label">Total Serangan</div>
      <div class="stat-val merah">{{ total }}</div>
    </div>
    <div class="stat">
      <div class="stat-label">IP Unik</div>
      <div class="stat-val kuning">{{ ip_unik }}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Port Terbanyak</div>
      <div class="stat-val hijau">{{ port_terbanyak }}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Serangan Terakhir</div>
      <div class="stat-val" style="font-size:14px; padding-top:6px">{{ terakhir }}</div>
    </div>
  </div>

  <h2>Log Serangan Terbaru</h2>
  {% if logs %}
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Waktu</th>
        <th>IP Penyerang</th>
        <th>Protokol</th>
        <th>Port</th>
        <th>Payload</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
      <tr>
        <td style="color:#555">{{ loop.revindex }}</td>
        <td>{{ log.waktu }}</td>
        <td style="font-family:monospace; color:#f0b429">{{ log.ip }}</td>
        <td>
          <span class="badge badge-{{ log.protokol | lower }}">{{ log.protokol }}</span>
        </td>
        <td style="font-family:monospace">{{ log.port }}</td>
        <td style="color:#888; font-size:12px">{{ log.payload[:60] }}{% if log.payload|length > 60 %}...{% endif %}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">
    Belum ada serangan terdeteksi.<br>
    Pastikan ESP32 sudah menyala dan terhubung ke server ini via Ngrok.
  </div>
  {% endif %}
</body>
</html>
"""

# ============================================
# ROUTE: Terima log dari ESP32
# ============================================
@app.route('/log', methods=['POST'])
def terima_log():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "pesan": "data kosong"}), 400

    # Tambah timestamp server
    data['waktu'] = datetime.now().strftime("%H:%M:%S")
    data['tanggal'] = datetime.now().strftime("%Y-%m-%d")

    # Simpan ke list
    log_serangan.append(data)

    # Batasi 200 log terbaru saja di memory
    if len(log_serangan) > 200:
        log_serangan.pop(0)

    # Simpan juga ke file JSON
    with open("log_serangan.json", "w") as f:
        json.dump(log_serangan, f, indent=2)

    print(f"[{data['waktu']}] ⚠  Serangan dari {data['ip']} ke port {data['port']} ({data['protokol']})")

    return jsonify({"status": "ok", "total": len(log_serangan)})

# ============================================
# ROUTE: Dashboard web
# ============================================
@app.route('/')
def dashboard():
    total     = len(log_serangan)
    ip_unik   = len(set(l['ip'] for l in log_serangan)) if log_serangan else 0
    terakhir  = log_serangan[-1]['waktu'] if log_serangan else "-"

    # Hitung port terbanyak
    if log_serangan:
        from collections import Counter
        port_count   = Counter(l['protokol'] for l in log_serangan)
        port_terbanyak = port_count.most_common(1)[0][0]
    else:
        port_terbanyak = "-"

    # Tampilkan 50 log terbaru, urutan terbaru di atas
    logs = list(reversed(log_serangan[-50:]))

    return render_template_string(
        DASHBOARD_HTML,
        logs=logs,
        total=total,
        ip_unik=ip_unik,
        port_terbanyak=port_terbanyak,
        terakhir=terakhir
    )

# ============================================
# ROUTE: API JSON (opsional, untuk debugging)
# ============================================
@app.route('/api/logs')
def api_logs():
    return jsonify({
        "total": len(log_serangan),
        "logs": list(reversed(log_serangan[-20:]))
    })

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    print("=================================")
    print("  IDS ESP32 - Server Python")
    print("=================================")
    print("Server berjalan di http://localhost:5000")
    print("Buka browser ke alamat di atas")
    print("Tekan Ctrl+C untuk berhenti")
    print("=================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
