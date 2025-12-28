import os
import gspread
import google.auth




# ============================================================
# 1. 接続設定・認証
# ============================================================


def get_connection():
    """Google Cloudの自動認証を使って接続"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials, project_id = google.auth.default(scopes=scopes)
    return gspread.authorize(credentials)




# ============================================================
# 2. メンション機能用 (参照系)
# ============================================================


def get_trigger_rules():
    print("Fetching Rules...")
    try:
        client = get_connection()
        sheet_id = os.environ.get("MEMBER_MANAGER_SHEET_ID")
        sheet = client.open_by_key(sheet_id).worksheet("Rules")
        records = sheet.get_all_records()
        
        rules_map = {}
        for row in records:
            trigger = str(row["Trigger"]).strip()
            channels_str = str(row["Allowed_Channels"])
            
            if channels_str.upper() == "ALL":
                channels = ["ALL"]
            else:
                channels = [ch.strip() for ch in channels_str.split(",") if ch.strip()]
            
            if trigger:
                rules_map[trigger] = channels
        return rules_map
    except Exception as e:
        print(f"Rules Error: {e}")
        return {}


def get_all_members():
    print("Fetching Members...")
    try:
        client = get_connection()
        sheet_id = os.environ.get("MEMBER_MANAGER_SHEET_ID")
        sheet = client.open_by_key(sheet_id).sheet1 
        records = sheet.get_all_records()
        
        member_list = []
        for row in records:
            raw_tags = str(row.get("Tags", "")).split(",")
            clean_tags = [t.strip() for t in raw_tags if t.strip()]
            member_list.append({
                "id": str(row["MemberID"]),
                "tags": clean_tags
            })
        return member_list
    except Exception as e:
        print(f"Member Error: {e}")
        return []




# ============================================================
# 3. 会計機能：書き込み (支出・収入)
# ============================================================


def add_expenditure_entry(data):
    """会計用スプシに書き込み (ずれを修正)"""
    try:
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")
        
        if not sheet_id:
            print("Error: ACCOUNTING_SHEET_ID is missing.")
            return False

        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("支出") 

        row = [
            data.get("日付", ""), 
            data.get("種類", ""),      
            data.get("セクション", ""), 
            data.get("内容", ""),
            data.get("内訳", ""), 
            data.get("金額", ""), 
            data.get("支払者", ""), 
            data.get("精算", ""), 
        ]
        
        sheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        import traceback
        print(f"Expenditure Write Error: {e}")
        traceback.print_exc()
        return False


def add_other_income_entry(data):
    print(f"[DEBUG] Adding other income: {data}")
    try:
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("その他収入")
        row = [
            data.get("日付", ""),
            data.get("内容", ""),
            data.get("金額", "")
        ]
        
        sheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"[DEBUG] Other Income Write Error: {e}")
        return False




# ============================================================
# 4. 会計機能：読み取り (部費支払い)
# ============================================================


def get_payment_status(name):
    print(f"--- [DEBUG] START: get_payment_status for '{name}' ---")
    try:
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("部費収入")
        all_values = sheet.get_all_values()
        if len(all_values) < 4:
            print("[DEBUG] ERROR: Sheet does not have enough rows (Header should be at Row 3).")
            return []

        headers = all_values[2]
        rows = all_values[3:]
        print(f"[DEBUG] Headers from Row 3: {headers}")
        search_name = name.replace(" ", "").replace("　", "")
        user_row = None
        name_col_idx = 2 
        
        if "名前" in headers:
            name_col_idx = headers.index("名前")
            print(f"[DEBUG] Found '名前' column at index: {name_col_idx}")

        for i, row in enumerate(rows):
            if len(row) <= name_col_idx: continue
            
            current_name = str(row[name_col_idx]).strip()
            clean_current_name = current_name.replace(" ", "").replace("　", "")
            
            if clean_current_name == search_name:
                print(f"[DEBUG] Match Found! Row: {i+4}, Name: '{current_name}'")
                user_row = row
                break

        if not user_row:
            print(f"[DEBUG] ERROR: Member '{name}' not found below C4.")
            return None

        months = ["9月", "10月", "11月", "12月", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
        paid_details = []

        for m in months:
            zen_m = m.translate(str.maketrans('0123456789', '０１２３４５６７８９'))
            m_idx = -1
            for idx, h in enumerate(headers):
                if h == m or h == zen_m:
                    m_idx = idx
                    break
            
            if m_idx != -1 and m_idx < len(user_row):
                val = str(user_row[m_idx]).strip()
                print(f"[DEBUG] Checking {m} (Col: {m_idx}): Value = '{val}'")
                if val:
                    paid_details.append(f"● {m}：{val}")

        print(f"--- [DEBUG] END: Found {len(paid_details)} entries ---")
        return paid_details

    except Exception as e:
        print(f"[DEBUG] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return []
    
