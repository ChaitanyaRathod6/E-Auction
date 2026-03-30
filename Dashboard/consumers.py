import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.group_name = f'auction_{self.auction_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from WebSocket (not used — bids come via view)
    async def receive(self, text_data):
        pass

    # Receive broadcast from group and send to WebSocket client
    async def auction_bid(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_bid',
            'amount': event['amount'],
            'bidder_name': event['bidder_name'],
            'bidder_initial': event['bidder_initial'],
            'bid_count': event['bid_count'],
            'min_next_bid': event['min_next_bid'],
        }))