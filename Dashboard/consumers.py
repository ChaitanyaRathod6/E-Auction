import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.group_name = f'auction_{self.auction_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def auction_bid(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_bid',
            'amount': event['amount'],
            'bidder_name': event['bidder_name'],
            'bidder_initial': event['bidder_initial'],
            'bid_count': event['bid_count'],
            'min_next_bid': event['min_next_bid'],
        }))


# ── NEW: Per-user dashboard notifications ──
class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    # Called when auction ends — sends popup to this user
    async def auction_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': event['notification_type'],  # 'buyer_won' or 'seller_payment_pending'
            'auction_id': event['auction_id'],
            'auction_name': event['auction_name'],
            'amount': event['amount'],
            'pay_url': event.get('pay_url', ''),
        }))