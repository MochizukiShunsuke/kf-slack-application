from listeners.views_accounting import (
    handle_menu_selection,
    handle_modal_update,
    handle_manual_expense_submission,
    handle_receipt_input,
    handle_membership_fee_submission,
    handle_other_income_submission
)

def register_view_router(app):
    # 1. メニュー選択
    app.view("accounting_menu_selection")(handle_menu_selection)
    
    # 2. モーダル内の動的更新（項目追加・削除など）
    app.action("add_item")(handle_modal_update)
    app.action("remove_item")(handle_modal_update)
    app.action("refresh_total")(handle_modal_update)
    
    # 3. 各機能の最終送信（Submit）
    app.view("manual_expense_submission")(handle_manual_expense_submission)
    app.view("accounting_receipt_input")(handle_receipt_input)
    app.view("membership_fee_submission")(handle_membership_fee_submission)
    app.view("other_income_submission")(handle_other_income_submission)