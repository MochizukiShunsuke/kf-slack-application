import os
import gspread
import google.auth
import logging

logger = logging.getLogger(__name__)


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
    except Exception:
        logger.exception("Get Trigger Rules Error")
        return None

def get_all_members():
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
    except Exception:
        logger.exception("Get All Members Error")
        return None

# ============================================================
# 3. 会計機能：書き込み (支出・収入)
# ============================================================

def add_expenditure_entry(data):
    try:
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")

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
    except Exception:
        logger.exception("Add Expenditure Entry Error")
        return False

def add_membership_fee_payment(name, month, payment_date):
    try:
        if not name: return False
        
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("部費収入")
        all_values = sheet.get_all_values()
        
        if len(all_values) < 4: return False
        headers = all_values[2]
        
        search_name = name.replace(" ", "").replace("　", "")
        name_col_idx = headers.index("名前") if "名前" in headers else 2
        
        row_index = -1
        for i, row in enumerate(all_values[3:], start=4):
            if len(row) > name_col_idx:
                clean_row_name = str(row[name_col_idx]).replace(" ", "").replace("　", "")
                if clean_row_name == search_name:
                    row_index = i
                    break
        
        if row_index == -1: return False
        
        zen_month = month.translate(str.maketrans('0123456789', '０１２３４５６７８９'))
        col_index = -1
        for idx, h in enumerate(headers, start=1):
            if h == month or h == zen_month:
                col_index = idx
                break
        
        if col_index == -1: return False
        sheet.update_cell(row_index, col_index, payment_date)
        return True
    except Exception:
        logger.exception("Add Membership Fee Payment Error")
        return False

def add_other_income_entry(data):
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
    except Exception:
        logger.exception("Add Other Income Entry Error")
        return False

# ============================================================
# 4. 会計機能：読み取り (部費支払い)
# ============================================================

def get_payment_status(name):
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
    except Exception:
        logger.exception("Get Payment Status Error")
        return None

def get_unpaid_months(name):
    try:
        if not name: return None
        
        client = get_connection()
        sheet_id = os.environ.get("ACCOUNTING_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("部費収入")
        all_values = sheet.get_all_values()
        
        if len(all_values) < 4: return None
        headers = all_values[2]
        rows = all_values[3:]
        
        search_name = name.replace(" ", "").replace("　", "")
        name_col_idx = headers.index("名前") if "名前" in headers else 2
        
        user_row = None
        for row in rows:
            if len(row) > name_col_idx:
                clean_row_name = str(row[name_col_idx]).replace(" ", "").replace("　", "")
                if clean_row_name == search_name:
                    user_row = row
                    break
        
        if not user_row: return None
        
        months = ["9月", "10月", "11月", "12月", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
        unpaid_months = []

        for m in months:
            zen_m = m.translate(str.maketrans('0123456789', '０１２３４５６７８９'))
            m_idx = next((idx for idx, h in enumerate(headers) if h == m or h == zen_m), -1)
            
            if m_idx != -1:
                val = str(user_row[m_idx]).strip() if m_idx < len(user_row) else ""
                if not val:
                    unpaid_months.append(m)
        
        return unpaid_months
    except Exception:
        logger.exception("Get Unpaid Months Error")
        return None

def get_member_name_by_id(slack_user_id):
    try:
        client = get_connection()
        sheet_id = os.environ.get("MEMBER_MANAGER_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1 
        data = sheet.get_all_values()

        if len(data) < 2: return None
        
        for row in data[1:]:
            if len(row) < 2: continue
            target_id = str(row[1]).replace('"', '').strip()
            if target_id == slack_user_id:
                official_name = str(row[0]).replace(" ", "").replace("　", "").strip()
                return official_name
        return None
    except Exception:
        logger.exception("Get Member Name By ID Error")
        return None

# ============================================================
# 5. 近況活動報告担当者催促
# ============================================================

def get_activity_report_mentions(month_str):
    try:
        client = get_connection()
        sheet_id = os.environ.get("ACTIVITY_REPORT_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet_monthly = spreadsheet.worksheet("担当者一覧")
        all_values = sheet_monthly.get_all_values()
        target_row = None

        for row in all_values[1:]:
            if str(row[0]).strip() == month_str:
                target_row = row
                break
        
        if not target_row:
            print(f"No assignees found for month: {month_str}")
            return ""
        
        assignee_names = [name for name in target_row[1:8] if name.strip()]
        sheet_members = spreadsheet.worksheet("メンバーID対応表")
        member_records = sheet_members.get_all_records()
        
        mentions = []
        for name in assignee_names:
            m = next((m for m in member_records if str(m.get("名前")).strip() == str(name).strip()), None)
            if m and m.get("メンバーID"):
                raw_id = str(m["メンバーID"]).replace('"', '').strip()
                mention = f"<@{raw_id}>" if not raw_id.startswith("<@") else raw_id
                mentions.append(mention)
        return " ".join(mentions)
    except Exception:
        logger.exception("Get Activity Report Mentions Error")
        return None