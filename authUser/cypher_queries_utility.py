from neomodel import db
import time
from datetime import datetime
from  uuid import uuid4
from neoUserModel.models import Channel

def exists_person_node(self_did):
	return db.cypher_query(
			f"""
				Optional match (n:Person{{did:$self_did}})
				return n is not null
			""",{"self_did":self_did}
		)[0][0][0]

def fetch_all_clubs(self_did,page_number=1):
	# start = time.time()
	offset = ((page_number or 1)*20)-20
	clubs = db.cypher_query(
			f"""
				call{{
					match (self:Person{{did:$self_did}})
					match (c:Club)-[:OWNER]->(n:Person)
					return {{
						club_id:c.club_id,
						club_name:c.club_name,
						description:c.description,
						category:c.category,
						profile_image:c.profile_image,
						cover_image:c.cover_image,
						created_at:c.create_at,
						member_count:size((c)<-[:MEMBER_OF]-(:Person)),
						is_member:exists((self)-[:MEMBER_OF]->(c)),
						owner:{{
							did:n.did,
							nick_name:n.nick_name,
							joined_at:n.created_at,
							kundli_attributes:n.person_kundli_attributes,
							zone:n.zone,
							like_count:n.likes,
							profile_pics:n.profile_pics
						}}

					}} as clubs_map order by clubs_map['member_count'] DESC skip $offset limit 20
				}} return collect(clubs_map)
 			""",{"self_did":self_did,"offset":offset}
 		)[0][0][0]
	# end = time.time()
	# print("time: ",end-start)
	return clubs



def fetch_user_clubs(self_did,page_number=1):
	# start = time.time()
	offset = ((page_number or 1)*20) - 20
	clubs = db.cypher_query(
			f"""
				call{{
					match (self:Person{{did:$self_did}})<-[:OWNER]-(c:Club)
					return {{
						club_id:c.club_id,
						club_name:c.club_name,
						description:c.description,
						category:c.category,
						profile_image:c.profile_image,
						cover_image:c.cover_image,
						created_at:c.create_at,
						member_count:size((c)<-[:MEMBER_OF]-(:Person)),
						is_member:exists((self)-[:MEMBER_OF]->(c)),
						owner:{{
							did:self.did,
							nick_name:self.nick_name,
							joined_at:self.created_at,
							kundli_attributes:self.person_kundli_attributes,
							zone:self.zone,
							like_count:self.likes,
							profile_pics:self.profile_pics
						}}
					}} as clubs_map order by clubs_map['like_count'] DESC skip $offset limit 20
				}}
				return collect(clubs_map)


			""",{"self_did":self_did,"offset":offset}
		)[0][0][0]
	# end = time.time()
	# print("time:",end-start)
	return clubs


def fetch_all_pages(self_did,page_number=1):
	# start=time.time()
	offset = ((page_number or 1)*20)-20
	pages = db.cypher_query(
			f"""
				call{{
					match (self:Person{{did:$self_did}})
					match (p:Page)-[:PAGE_OWNER]->(n:Person)
					return {{
						page_id:p.page_id,
						page_name:p.page_name,
						profile_image:p.profile_image,
						cover_image:p.cover_image,
						created_at:p.created_at,
						like_count:p.likes,
						is_like_to:exists((self)-[:Like]->(p)),
						owner:{{
							did:n.did,
							nick_name:n.nick_name,
							joined_at:n.created_at,
							kundli_attributes:n.person_kundli_attributes,
							zone:n.zone,
							like_count:n.likes,
							profile_pics:n.profile_pics
						}}

					}} as pages_map order by pages_map['like_count'] DESC skip $offset limit 20
				}} return collect(pages_map)
			""",{"self_did":self_did,"offset":offset}
		)[0][0][0]
	# end = time.time()
	# print("time:",end-start)
	return pages


def fetch_user_pages(self_did,page_number=1):
	# start = time.time()
	offset = ((page_number or 1)*20) - 20
	page_list = []
	pages = db.cypher_query(
			f"""
				call{{
					match (self:Person{{did:$self_did}})<-[:PAGE_OWNER]-(p:Page)
					return {{
						page_id:p.page_id,
						page_name:p.page_name,
						profile_image:p.profile_image,
						cover_image:p.cover_image,
						created_at:p.created_at,
						like_count:p.likes,
						is_like_to:exists((self)-[:Like]->(p)),
						owner:{{
							did:self.did,
							nick_name:self.nick_name,
							joined_at:self.created_at,
							kundli_attributes:self.person_kundli_attributes,
							zone:self.zone,
							like_count:self.likes,
							profile_pics:self.profile_pics
						}}
					}} as pages_map order by pages_map['like_count'] DESC skip $offset limit 20
				}}
				return collect(pages_map)


			""",{"self_did":self_did,"offset":offset}
		)[0][0][0]
	# end = time.time()
	# print("time:",end-start)
	return pages



	# def create_message(text,from_id,to_id,room_id):
	# 	try:
	# 		result = db.cypher_query(
	# 				"""
	# 					match (room:channel{room_id:$room_id}
	# 					create (message:Message $props)
	# 					create (room)-[:CHANNEL]-(message)
	# 					return true
	#  				""",{
	# 					'from_id':from_id,
	# 					'to_id':to_id,
	# 					'room_id':room_id,
	# 					'props':{
	# 						'text':text,
	# 						'message_from':from_id,
	# 						'message_to':to_id
	# 					}
	# 				}
	# 			)[0][0][0]

	# 		return result
	# 	except:
	# 		return False



def fetch_friend_list(self_did,page_number=1):
	# start = time.time()
	offset = ((page_number or 1)*20) - 20
	page_list = []
	friend_list = db.cypher_query(
			"""
				call{
					match (self:Person{did:$self_did})-[frel:FRIEND]-(friend:Person)
					return {
						requested_date : frel.requested_date,
						aceepted_date : frel.accepted_date,
						did : friend.did,
						nick_name : friend.nick_name,
						kundli_attributes : friend.person_kundli_attributes,
						joined_at : friend.created_at,
						zone : friend.zone,
						like_count : friend.likes,
						profile_pics : friend.profile_pics,
						channel_room_code : frel.chat_room_id
					} as result order by result['accepted_date'] DESC skip $offset limit 20
				}
				return collect(result)
			""",{"self_did":self_did,"offset":offset}
		)[0][0][0]
	# end = time.time()
	# print("time:",end-start)
	return friend_list




def get_or_create_channel(room_id,self_did,consumer_did):
	result = db.cypher_query(
			"""
				match (p1:Person{did:$self_did})
				match (p2:Person{did:$consumer_did})
				merge (p1)-[:CHANNEL_MEMBER]->(c:Channel{room_id:$room_id})<-[:CHANNEL_MEMBER]-(p2)
				on match
					set c.is_created = false
				on create
					set c.is_created = true
				return c
			""",{'self_did':self_did,'room_id':room_id,'consumer_did':consumer_did}
		)[0][0][0]
	channel_obj = Channel.inflate(result)
	if channel_obj.is_created:
		channel_obj.created_at = datetime.now()
		channel_obj.save()
	# channel_obj.created_at = datetime.now()
	return channel_obj


# def create_message_in_db(text,room_id,from_id,to_id):
# 	result = db.cypher_query(
# 			"""
# 				create (m:Message{text:$text,})
# 			""",{'text':text,'room_id':room_id,'from_id':from_id,'to_id':to_id}
# 		)



@db.transaction
def make_friend(person_requested,target_person):
	request_rel = person_requested.request.relationship(target_person)
	# requested_date = request_rel.requested_date
	# transaction_id = request_rel.transaction_id
	person_requested.request.disconnect(target_person)

	rel = target_person.friends.connect(person_requested)
	rel.accepted_date = datetime.now()
	rel.requested_date = request_rel.requested_date
	rel.transaction_id = request_rel.transaction_id
	rel.chat_room_id = str(uuid4())
	rel.save()