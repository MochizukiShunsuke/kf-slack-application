from listeners.accounting_view_listener import (
    handle_menu_selection,
    handle_modal_update,
    handle_manual_expense_submission,
    handle_receipt_input_from_command,
    handle_receipt_shortcut_submission,
    handle_membership_fee_status_submission,
    handle_membership_fee_payment_name_submission,
    handle_membership_fee_payment_final_submission,
    handle_other_income_submission
)
from listeners.rag_view_listener import handle_rag_submission_ack, handle_rag_submission_lazy

def register_view_router(slack_app):

    ### 会計機能 ###

    # 1. メニュー選択
    slack_app.view("accounting_menu_selection")(handle_menu_selection)
    
    # 2. モーダル内の動的更新（項目追加・削除など）
    slack_app.action("add_item")(handle_modal_update)
    slack_app.action("remove_item")(handle_modal_update)
    slack_app.action("refresh_total")(handle_modal_update)

    slack_app.view("membership_fee_payment_name_submission")(handle_membership_fee_payment_name_submission)
    
    # 3. 各機能の最終送信（Submit）
    slack_app.view("manual_expense_submission")(handle_manual_expense_submission)
    slack_app.view("accounting_receipt_input")(handle_receipt_input_from_command)

    slack_app.view("accounting_receipt_input_shortcut")(handle_receipt_shortcut_submission)

    slack_app.view("membership_fee_status_submission")(handle_membership_fee_status_submission)
    slack_app.view("membership_fee_payment_final_submission")(handle_membership_fee_payment_final_submission)
    slack_app.view("other_income_submission")(handle_other_income_submission)

    ### RAG機能 ###
    
    # 1. RAGパーソナルクエスチョン
    slack_app.view("rag_question_submission")(
        ack=handle_rag_submission_ack,
        lazy=[handle_rag_submission_lazy]
    )