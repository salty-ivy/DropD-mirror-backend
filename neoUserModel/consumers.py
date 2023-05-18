import json
from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer
from channels.db import database_sync_to_async
from .models import Person,Message,Channel
from asgiref.sync import async_to_sync
from authUser.cypher_queries_utility import get_or_create_channel
from neomodel import db
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):

	@database_sync_to_async
	@db.transaction
	def create_message(self,room_id,text,from_id,to_id):
		channel = get_or_create_channel(room_id,int(from_id),int(to_id))
		message = Message(text=text,message_from=from_id,message_to=to_id).save()
		message.channel.connect(channel)
		message.save()


	async def connect(self):
		# print(self.scope['user'])
		if not self.scope['user'].is_authenticated:
			print("Unauthorized access, invalid token")
			await self.close()
		self.room_name = self.scope['url_route']['kwargs']['code']
		self.room_group_name = f"chat_{self.room_name}"

		await self.channel_layer.group_add(
				self.room_group_name,
				self.channel_name
			)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
				self.room_group_name,
				self.channel_name
			)

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json['message']
		to_id = text_data_json['to_id']
		await self.create_message(self.room_name,message,self.scope['user'].id,to_id)
		await self.channel_layer.group_send(
				self.room_group_name,
				{
					'type':'chat_message',
					'message':message,
				}
			)

	async def chat_message(self,event):
		message = event['message']

		await self.send(text_data=json.dumps({
				'message':message,
			}))