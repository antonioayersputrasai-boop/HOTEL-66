import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="StayVista | Hotel Experience", page_icon="🏨", layout="wide", initial_sidebar_state="expanded")
DATA_FILE = Path(__file__).parent / "data_kamar.csv"
USERNAME, PASSWORD = "ICIKIWIR", "ICIKIWIR123"
ROOM_INVENTORY = {"Standard": 5, "Deluxe": 3, "Suite": 2}
ROOM_RATES = {"Standard": 450000, "Deluxe": 750000, "Suite": 1200000}
KOLOM = ["tanggal_checkin", "tanggal_checkout", "tanggal_pesan", "kode_pemesanan", "tipe_kamar", "status_kamar", "kanal_pemesanan", "status_reservasi", "pendapatan"]

st.markdown("""
<style>
:root { --sv-gold:#c7a45b; --sv-navy:#102438; }
[data-testid="stAppViewContainer"] { background: linear-gradient(180deg, rgba(199,164,91,.045), transparent 340px); }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#102438,#183b50); }
[data-testid="stSidebar"] * { color:#f5f7fa !important; }
.sv-hero { padding:36px 34px; border-radius:22px; color:#fff; background:linear-gradient(100deg,rgba(9,25,48,.97),rgba(14,49,72,.78)),url('https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1800&q=85'); background-size:cover;background-position:center;border:1px solid rgba(199,164,91,.55);margin-bottom:20px; }
.sv-kicker {color:#e6c777;font-size:11px;font-weight:800;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px;}
.sv-hero h1 {color:white;font-size:clamp(30px,4vw,48px);line-height:1.1;margin:0 0 12px;font-weight:800;}
.sv-hero p {color:#edf2f7;font-size:15px;line-height:1.7;max-width:720px;margin:0;}
.sv-section {font-size:12px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#b08a3e;margin:22px 0 8px;}
.sv-card {padding:18px 20px;border:1px solid rgba(160,160,160,.25);border-radius:16px;background:rgba(128,128,128,.055);height:100%;}
.sv-card h3 {margin:0 0 8px;font-size:18px;}
.sv-muted {opacity:.78;font-size:13px;line-height:1.6;}
div[data-testid="stMetric"] {background:rgba(128,128,128,.06);border:1px solid rgba(150,150,150,.2);padding:14px 16px;border-radius:15px;}
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] button {border-radius:10px;font-weight:650;}
</style>
""", unsafe_allow_html=True)

def load_data():
    if not DATA_FILE.exists():
        pd.DataFrame(columns=KOLOM).to_csv(DATA_FILE, index=False)
    try:
        df = pd.read_csv(DATA_FILE)
    except (pd.errors.EmptyDataError, UnicodeDecodeError):
        df = pd.DataFrame(columns=KOLOM)
    for col in KOLOM:
        if col not in df.columns: df[col] = pd.NA
    for col in ["tanggal_checkin", "tanggal_checkout", "tanggal_pesan"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["kode_pemesanan", "tipe_kamar", "status_kamar", "kanal_pemesanan", "status_reservasi"]:
        df[col] = df[col].fillna("").astype(str)
    df["pendapatan"] = df.apply(hitung_pendapatan, axis=1)
    return df[KOLOM]

def hitung_pendapatan(row):
    status = str(row.get("status_reservasi", ""))
    tipe = str(row.get("tipe_kamar", ""))
    mulai, selesai = pd.to_datetime(row.get("tanggal_checkin"), errors="coerce"), pd.to_datetime(row.get("tanggal_checkout"), errors="coerce")
    if status not in ["Check-in", "Check-out"] or tipe not in ROOM_RATES or pd.isna(mulai) or pd.isna(selesai): return 0
    malam = max((selesai.date() - mulai.date()).days, 0)
    return ROOM_RATES[tipe] * malam

def save_data(df):
    hasil = df.copy()
    hasil["pendapatan"] = hasil.apply(hitung_pendapatan, axis=1)
    for col in ["tanggal_checkin", "tanggal_checkout", "tanggal_pesan"]:
        hasil[col] = pd.to_datetime(hasil[col], errors="coerce").dt.strftime("%Y-%m-%d")
    hasil.to_csv(DATA_FILE, index=False)

def rupiah(nilai): return "Rp " + f"{float(nilai):,.0f}".replace(",", ".")

def cek_ketersediaan(df, checkin, checkout):
    aktif = df[df["status_reservasi"].isin(["Booked", "Check-in"])].copy()
    hasil = []
    for tipe, kapasitas in ROOM_INVENTORY.items():
        puncak = 0
        for malam in pd.date_range(checkin, checkout - timedelta(days=1)):
            mask = ((aktif["tipe_kamar"] == tipe) & (aktif["tanggal_checkin"].dt.date <= malam.date()) & (aktif["tanggal_checkout"].dt.date > malam.date()))
            puncak = max(puncak, int(mask.sum()))
        tersedia = max(kapasitas - puncak, 0)
        hasil.append({"Tipe Kamar": tipe, "Tarif / malam": ROOM_RATES[tipe], "Kapasitas": kapasitas, "Terpakai": puncak, "Tersedia": tersedia, "Status": "PENUH" if tersedia == 0 else "TERSEDIA"})
    return pd.DataFrame(hasil)

def chart_theme(fig):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=12,r=12,t=35,b=12), legend_title_text="")
    return fig

if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.markdown("<div style='text-align:center;font-size:54px;margin-top:30px'>🏨</div>", unsafe_allow_html=True)
    st.title("StayVista Hotel Experience")
    st.caption("Satu tempat untuk reservasi, operasional kamar, dan performa hotel.")
    with st.form("form_login"):
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        masuk = st.form_submit_button("Masuk ke StayVista", use_container_width=True)
    if masuk:
        if user == USERNAME and password == PASSWORD:
            st.session_state.login = True; st.rerun()
        else: st.error("Username atau password salah.")
    st.info("SILAHKAN LOGIN")
    st.stop()

df = load_data()
st.sidebar.markdown("# 🏨 StayVista")
st.sidebar.caption("HOTEL MANAGEMENT SUITE")
st.sidebar.divider()
halaman = st.sidebar.radio("NAVIGASI", ["Home", "Cek Ketersediaan Kamar", "Dashboard Analytics", "Manajemen Data"])
st.sidebar.divider()
st.sidebar.caption(f"Total reservasi tercatat: {len(df)}")
if st.sidebar.button("Keluar", use_container_width=True): st.session_state.login = False; st.rerun()

# HOME
if halaman == "Home":
    st.markdown("<div class='sv-hero'><div class='sv-kicker'>Welcome to StayVista</div><h1>Stay exceptional.<br>Feel at home.</h1><p>Kelola pengalaman menginap dengan lebih mudah. Pantau kamar, reservasi, dan pendapatan hotel dalam satu ruang kerja yang elegan.</p></div>", unsafe_allow_html=True)
    checkin_count = int((df["status_reservasi"] == "Check-in").sum())
    pendapatan_total = int(df["pendapatan"].sum())
    a,b,c,d = st.columns(4)
    a.metric("Total Reservasi", len(df))
    b.metric("Tamu Check-in", checkin_count)
    c.metric("Kamar Tersedia", sum(ROOM_INVENTORY.values()) - int(df[df["status_reservasi"].isin(["Booked","Check-in"])].shape[0]))
    d.metric("Pendapatan Terealisasi", rupiah(pendapatan_total))
    st.caption("Pendapatan dimulai dari Rp 0 dan dihitung otomatis dari reservasi berstatus Check-in atau Check-out: tarif kamar × jumlah malam. Reservasi lama tidak disertakan pada file versi ini.")
    st.markdown("<div class='sv-section'>Pilih pengalaman menginap</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    room_details = [("Standard", "Praktis dan nyaman untuk kebutuhan menginap esensial.", "photo-1611892440504-42a792e24d32"),("Deluxe", "Ruang lebih lega dengan nuansa elegan dan menenangkan.", "photo-1590490360182-c33d57733427"),("Suite", "Pilihan premium dengan ruang dan kenyamanan ekstra.", "photo-1582719478250-c89cae4dc85b")]
    for col,(name,desc,img) in zip(cols,room_details):
        with col:
            st.image(f"https://images.unsplash.com/{img}?auto=format&fit=crop&w=900&q=80", use_container_width=True)
            st.markdown(f"<div class='sv-card'><h3>{name} Room</h3><div class='sv-muted'>{desc}</div><br><b>{rupiah(ROOM_RATES[name])}</b> <span class='sv-muted'>/ malam</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='sv-section'>Ringkasan operasional</div>", unsafe_allow_html=True)
    left,right = st.columns([1.1,1])
    with left:
        st.markdown("<div class='sv-card'><h3>✨ Semua dalam kendali</h3><div class='sv-muted'>Cek kamar berdasarkan tanggal, catat reservasi baru, ubah status tamu saat check-in, lalu pantau perkembangan bisnis dari grafik analitik.</div></div>", unsafe_allow_html=True)
    with right:
        by_status = df["status_reservasi"].value_counts().reindex(["Booked","Check-in","Check-out","Cancelled"], fill_value=0).reset_index()
        by_status.columns = ["Status", "Jumlah"]
        if len(df): st.plotly_chart(chart_theme(px.pie(by_status, names="Status", values="Jumlah", hole=.62, title="Status reservasi")), use_container_width=True)
        else: st.info("Belum ada reservasi. Tambahkan data pertama melalui menu Manajemen Data.")

# AVAILABILITY
elif halaman == "Cek Ketersediaan Kamar":
    st.markdown("<div class='sv-hero'><div class='sv-kicker'>Room finder</div><h1>Temukan kamar yang tepat.</h1><p>Pilih tanggal menginap dan lihat pilihan kamar yang tersedia sebelum menerima reservasi.</p></div>", unsafe_allow_html=True)
    x,y = st.columns(2); hari_ini = date.today()
    checkin = x.date_input("📅 Check-in", value=hari_ini, key="pilih_checkin")
    checkout = y.date_input("📅 Check-out", value=hari_ini+timedelta(days=1), min_value=checkin+timedelta(days=1), key="pilih_checkout")
    if checkout <= checkin: st.error("Tanggal check-out harus setelah check-in.")
    else:
        hasil = cek_ketersediaan(df, checkin, checkout)
        malam = (checkout-checkin).days
        m1,m2,m3 = st.columns(3); m1.metric("Lama Menginap", f"{malam} malam"); m2.metric("Total Kapasitas", int(hasil.Kapasitas.sum())); m3.metric("Kamar Tersedia", int(hasil.Tersedia.sum()))
        st.markdown(f"<div class='sv-section'>Pilihan untuk {checkin:%d %b %Y} – {checkout:%d %b %Y}</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for col,(_,r) in zip(cols,hasil.iterrows()):
            with col:
                with st.container(border=True):
                    st.subheader(f"🛏️ {r['Tipe Kamar']}")
                    st.metric("Kamar tersedia", f"{int(r['Tersedia'])} / {int(r['Kapasitas'])}")
                    st.progress(int(r["Tersedia"])/int(r["Kapasitas"]) if r["Kapasitas"] else 0)
                    st.write(f"**{rupiah(r['Tarif / malam'])}** / malam")
                    st.caption(f"Estimasi {malam} malam: {rupiah(r['Tarif / malam']*malam)}")
                    if r["Tersedia"] == 0: st.error("Tidak tersedia untuk tanggal ini")
                    elif r["Tersedia"] <= 1: st.warning("Sisa kamar terbatas")
                    else: st.success("Siap dipesan")
        st.dataframe(hasil, use_container_width=True, hide_index=True)
        st.caption("Kapasitas simulasi: Standard 5, Deluxe 3, Suite 2. Reservasi Booked dan Check-in memblokir kamar; Check-out dan Cancelled tidak.")

# ANALYTICS
elif halaman == "Dashboard Analytics":
    st.markdown("<div class='sv-hero'><div class='sv-kicker'>Performance studio</div><h1>Insight di balik setiap stay.</h1><p>Ubah data reservasi menjadi gambaran performa hotel, tren tamu, dan pendapatan yang terealisasi.</p></div>", unsafe_allow_html=True)
    if df.empty:
        st.info("Analytics akan tampil setelah kamu menambahkan reservasi di menu Manajemen Data.")
        st.metric("Pendapatan saat ini", rupiah(0))
    else:
        valid_dates = df["tanggal_checkin"].dropna()
        if valid_dates.empty: data = df.copy()
        else:
            ca,cb = st.columns(2); mulai = ca.date_input("Check-in mulai", value=valid_dates.min().date(), key="filter_mulai"); akhir = cb.date_input("Check-in sampai", value=max(valid_dates.min().date(),valid_dates.max().date()), key="filter_akhir")
            data = df[(df["tanggal_checkin"].dt.date >= mulai) & (df["tanggal_checkin"].dt.date <= akhir)] if mulai <= akhir else df.iloc[0:0]
        status_pilih = st.multiselect("Filter status reservasi", ["Booked","Check-in","Check-out","Cancelled"], default=["Booked","Check-in","Check-out","Cancelled"])
        data = data[data["status_reservasi"].isin(status_pilih)]
        pendapatan = int(data["pendapatan"].sum()); aktif = int(data["status_reservasi"].isin(["Booked","Check-in"]).sum()); checked = int((data["status_reservasi"]=="Check-in").sum())
        a,b,c,d = st.columns(4); a.metric("Reservasi",len(data)); b.metric("Tamu Check-in",checked); c.metric("Reservasi Aktif",aktif); d.metric("Pendapatan",rupiah(pendapatan))
        left,right = st.columns(2)
        with left:
            st.subheader("📦 Minat tipe kamar")
            chart = data.groupby("tipe_kamar").size().reindex(list(ROOM_INVENTORY),fill_value=0).reset_index(); chart.columns=["Tipe Kamar","Reservasi"]
            st.plotly_chart(chart_theme(px.bar(chart,x="Tipe Kamar",y="Reservasi",color="Tipe Kamar",text_auto=True,title="Reservasi berdasarkan tipe kamar")),use_container_width=True)
        with right:
            st.subheader("🧭 Kanal pemesanan")
            channel = data.groupby("kanal_pemesanan").size().reset_index(name="Reservasi")
            if not channel.empty: st.plotly_chart(chart_theme(px.pie(channel,names="kanal_pemesanan",values="Reservasi",hole=.58,title="Kontribusi kanal")),use_container_width=True)
            else: st.info("Belum ada kanal pemesanan pada filter ini.")
        st.subheader("💰 Pendapatan per tipe kamar")
        rev = data.groupby("tipe_kamar")["pendapatan"].sum().reindex(list(ROOM_RATES),fill_value=0).reset_index(); rev.columns=["Tipe Kamar","Pendapatan"]
        st.plotly_chart(chart_theme(px.bar(rev,x="Tipe Kamar",y="Pendapatan",color="Tipe Kamar",text_auto=True,title="Pendapatan terealisasi per tipe kamar")),use_container_width=True)
        st.subheader("📈 Tren reservasi")
        trend = data.dropna(subset=["tanggal_pesan"]).groupby(data["tanggal_pesan".strip()].dt.date).size().reset_index(name="Reservasi") if not data.dropna(subset=["tanggal_pesan"]).empty else pd.DataFrame()
        if not trend.empty:
            trend.columns=["Tanggal Pemesanan","Reservasi"]
            st.plotly_chart(chart_theme(px.line(trend,x="Tanggal Pemesanan",y="Reservasi",markers=True,title="Pemesanan dari waktu ke waktu")),use_container_width=True)
        st.subheader("Data yang dianalisis")
        st.dataframe(data, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Unduh hasil analitik (CSV)", data.to_csv(index=False).encode("utf-8-sig"), "ringkasan_perhotelan.csv", "text/csv")

# MANAGEMENT
elif halaman == "Manajemen Data":
    st.markdown("<div class='sv-hero'><div class='sv-kicker'>Reservation desk</div><h1>Catat setiap kedatangan.</h1><p>Tambahkan reservasi baru, perbarui status tamu saat check-in, dan kelola data yang benar-benar kamu masukkan.</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='sv-section'>Tambah reservasi baru</div>", unsafe_allow_html=True)
    with st.form("form_reservasi", clear_on_submit=True):
        c1,c2=st.columns(2); kode=c1.text_input("Kode pemesanan",placeholder="RES-2001"); tipe=c2.selectbox("Tipe kamar",list(ROOM_INVENTORY),format_func=lambda t:f"{t} — {rupiah(ROOM_RATES[t])}/malam")
        c3,c4=st.columns(2); checkin_baru=c3.date_input("Tanggal check-in",value=date.today(),key="input_checkin"); checkout_baru=c4.date_input("Tanggal check-out",value=date.today()+timedelta(days=1),min_value=date.today()+timedelta(days=1),key="input_checkout")
        c5,c6=st.columns(2); tanggal_pesan=c5.date_input("Tanggal pemesanan",value=date.today(),key="input_pesan"); status_kamar=c6.selectbox("Status kebersihan",["Clean","Dirty","Under Maintenance"])
        c7,c8=st.columns(2); kanal=c7.selectbox("Kanal pemesanan",["Direct Website","Travel Agent Online","Walk-in"]); status_reservasi=c8.selectbox("Status reservasi",["Booked","Check-in","Check-out","Cancelled"],index=0)
        st.caption("Pendapatan otomatis dihitung berdasarkan tipe kamar dan lama menginap. Status Booked/Cancelled belum menghasilkan pendapatan; Check-in/Check-out dihitung sebagai pendapatan terealisasi.")
        estimasi=ROOM_RATES[tipe]*max((checkout_baru-checkin_baru).days,0)
        st.info(f"Tarif {tipe}: {rupiah(ROOM_RATES[tipe])}/malam · Estimasi pendapatan jika sudah check-in: {rupiah(estimasi)}")
        simpan=st.form_submit_button("＋ Simpan reservasi baru",use_container_width=True)
    if simpan:
        if not kode.strip(): st.error("Kode pemesanan harus diisi.")
        elif checkout_baru<=checkin_baru: st.error("Tanggal check-out harus setelah check-in.")
        elif kode.strip() in df["kode_pemesanan"].values: st.error("Kode pemesanan sudah digunakan. Gunakan kode yang berbeda.")
        else:
            penuh=False
            if status_reservasi in ["Booked","Check-in"]:
                aktif=df[df["status_reservasi"].isin(["Booked","Check-in"])]
                for malam in pd.date_range(checkin_baru,checkout_baru-timedelta(days=1)):
                    mask=(aktif["tipe_kamar"].eq(tipe)&(aktif["tanggal_checkin"].dt.date<=malam.date())&(aktif["tanggal_checkout"].dt.date>malam.date()))
                    if int(mask.sum())>=ROOM_INVENTORY[tipe]: penuh=True; break
            if penuh: st.error(f"Kamar {tipe} penuh pada salah satu tanggal yang dipilih. Pilih tanggal atau tipe lain.")
            else:
                baru=pd.DataFrame([{"tanggal_checkin":pd.Timestamp(checkin_baru),"tanggal_checkout":pd.Timestamp(checkout_baru),"tanggal_pesan":pd.Timestamp(tanggal_pesan),"kode_pemesanan":kode.strip(),"tipe_kamar":tipe,"status_kamar":status_kamar,"kanal_pemesanan":kanal,"status_reservasi":status_reservasi,"pendapatan":0}])
                df=pd.concat([df,baru],ignore_index=True); save_data(df); st.success("Reservasi baru berhasil disimpan. Data lama tidak dibuat ulang."); st.rerun()
    st.markdown("<div class='sv-section'>Perbarui status reservasi</div>",unsafe_allow_html=True)
    if df.empty: st.info("Belum ada data. Tambahkan reservasi pertama melalui formulir di atas.")
    else:
        with st.form("form_status"):
            kode_opsi=df["kode_pemesanan"].tolist(); pilih_kode=st.selectbox("Pilih kode reservasi",kode_opsi); status_baru=st.selectbox("Status terbaru",["Booked","Check-in","Check-out","Cancelled"],index=0)
            update=st.form_submit_button("Perbarui status",use_container_width=True)
        if update:
            idx=df.index[df["kode_pemesanan"]==pilih_kode][0]; df.loc[idx,"status_reservasi"]=status_baru; save_data(df); st.success(f"Status {pilih_kode} diperbarui menjadi {status_baru}."); st.rerun()
        st.markdown("<div class='sv-section'>Data reservasi tersimpan</div>",unsafe_allow_html=True)
        view=df.copy()
        for col in ["tanggal_checkin","tanggal_checkout","tanggal_pesan"]: view[col]=view[col].dt.strftime("%Y-%m-%d")
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.download_button("⬇️ Unduh semua data (CSV)",view.to_csv(index=False).encode("utf-8-sig"),"data_kamar.csv","text/csv")
        st.caption("Semua reservasi yang terlihat berasal dari data yang kamu input dan disimpan ke data_kamar.csv. Data tersimpan akan tetap ada setelah aplikasi dibuka ulang.")
