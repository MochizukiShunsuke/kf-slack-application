from config import PC_RESERVATION_CHANNELS
from listeners.pc_reservation_listener import handle_pc_reaction


def register_reaction_router(slack_app):
    @slack_app.event("reaction_added")
    def reaction_added_events(event, client, say, body):
        channel_id = event.get("item", {}).get("channel")
        
        # 監視対象のチャンネル以外は無視
        if channel_id in PC_RESERVATION_CHANNELS:
            print(channel_id)
            handle_pc_reaction(event, client, say)