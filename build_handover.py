import os, datetime, shutil

def build_handover(client, niche, support_zalo="090xxxxxxx", exe_path="dist/VN_SME_Ledger/VN_SME_Ledger.exe"):
    folder = f"handover_{client.replace(' ','_')}"
    os.makedirs(folder, exist_ok=True)
    
    # Copy core assets
    for d in ["data","presets","templates","invoices","contracts"]:
        os.makedirs(f"{folder}/{d}", exist_ok=True)
    if os.path.exists(exe_path):
        shutil.copy(exe_path, f"{folder}/VN_SME_Ledger.exe")
        
    # Generate README
    txt = f"""📦 BO PHAN MEM KE TOAN SME - {client.upper()}
📅 Ngay ban giao: {datetime.date.today():%d/%m/%Y} | 🏢 Nganh: {niche}
🔑 HUONG DAN NHANH:
1. Chay VN_SME_Ledger.exe (Khong can cai dat, chay offline 100%)
2. Tab Ledger -> Chon loai giao dich -> Nhap so tien -> Post (Tu dong DR=CR, map TT133)
3. Tab Invoices -> Tao hoa don PDF song ngu -> Gui KH qua Zalo/Email
4. Keo tha anh hoa don vao cua so -> AI offline tu doc & phan loai chi phi
5. Co mang -> Bam "Sync & Dashboard" de cap nhat thue & xem bieu do dong tien
🛡️ BAO MAT & HO TRO:
- Du lieu luu tren may ban. Cloud chi dong bo khi ban bam nut.
- Remote support qua AnyDesk (chi ket noi khi ban cap quyen 1 lan).
- Zalo ho tro: {support_zalo} | Phan hoi trong 2h gio hanh chinh.
⚠️ PHAP LY: Hoa don thuong mai noi bo. De nop thue dien tu, xuat file XLSX (Tab Ledger) & upload len cong thong tin GDT.
✅ Xac nhan ban giao: ___________________  Ngay: ___________
"""
    with open(f"{folder}/README_{client.replace(' ','_')}.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"✅ Ready: {folder}/ → ZIP & send to client.")

if __name__ == "__main__":
    build_handover("Tiem Photocopy Minh Anh", "photocopy_print")
