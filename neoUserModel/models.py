from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    IntegerProperty,
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom,
    Relationship,
    cardinality,
    ArrayProperty,
    BooleanProperty,
    DateTimeProperty,
    DateTimeFormatProperty,
)
from datetime import datetime,timedelta
# from neomodel import db
import time
import asyncio
from django_neomodel import DjangoNode
from uuid import uuid4

def random_room_id():
    return str(uuid4())

class FriendRel(StructuredRel):
    accepted_date = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")
    requested_date = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")
    transaction_id = StringProperty()
    chat_room_id = StringProperty(max_length=200,editable=False)


    # def post_save(self):
    #     channel = Channel(room_id = self.chat_room_id).save()
    #     channel.members.connect(self.start_node())
    #     channel.members.connect(self.end_node())
    #     channel.save()



class RequestRel(StructuredRel):
    requested_date = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")
    transaction_id = StringProperty()

class LikeRel(StructuredRel):
    liked_at = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")



class Person(DjangoNode):
    uid = UniqueIdProperty(primary_key=True)
    # uid = IntegerProperty(unique_index=True)
    # choices = {'male':'Male','female':'Female','genderqueer':'Genderqueer'}
    # gender_preference_choices = {'male':'Male','female':'Female','genderqueer':'Genderqueer'}
    zone_choices = {'love grounds':'LG','open marriage commune':'OMC','seniors in love again':'SIL'}
    did = IntegerProperty(unique_index=True,required=True)
    phone = IntegerProperty(defualt=None)
    email = StringProperty(default=None)
    nick_name = StringProperty(default=None)
    profile_pics = ArrayProperty(StringProperty(),)
    age = IntegerProperty(defualt=None)
    gender = StringProperty(default=None)
    gender_preference = StringProperty(default=None)
    zone = StringProperty(default=None)
    person_kundli_attributes = ArrayProperty(StringProperty(),default=None)
    partner_kundli_attributes = ArrayProperty(StringProperty(),default=None)
    interests = ArrayProperty(StringProperty(),default=None)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")
    city = StringProperty(default=None)
    marital_status = StringProperty(default=None)
    full_name = StringProperty(default=None)
    year_of_birth = IntegerProperty(default=None)
    country = StringProperty(default=None)
    likes = IntegerProperty(default=0)
    bio = StringProperty(default=None)
    language_preference1 = StringProperty(default=None)
    language_preference2 = StringProperty(default=None)
    language_preference3 = StringProperty(default=None)
    like_count = IntegerProperty(default=0)

    friends = Relationship('Person','FRIEND',model=FriendRel)
    posts = RelationshipTo('Post','POST_FROM')
    clubs = RelationshipTo('Club','MEMBER_OF')
    like  = RelationshipFrom('Person','likes',model=LikeRel)
    request = RelationshipFrom('Person','FRIEND_REQUEST',model=RequestRel)
    # request_sent = RelationshipTo('Person','FRIEND_REQUEST',model=RequestRel)
    sent_request = RelationshipTo('Person','FRIEND_REQUEST',model=RequestRel)
    pages = Relationship('Page','PAGE_OWNER')
    channels = RelationshipTo('Channel','CHANNEL_MEMBER')


    def __str__(self):
        return f"{self.email}--{self.phone}"

    class Meta:
        app_label = "neoUserModel"
        verbose_name_plural = "Persons"


    def completeCheck(self):
        check_elements = (
            (self.email,"email"),
            (self.interests,"interests"),
            (self.profile_pics,"profile_pics"),
            (self.nick_name,"nick_name"),
            (self.gender,"gender"),
            (self.gender_preference,"gender_preference"),
            (self.person_kundli_attributes,"person_kundli_attributes"),
            (self.partner_kundli_attributes,"partner_kundli_attributes"),
            (self.zone,"zone"),
        )

        for each in check_elements:
            if each[0] is None:
                return each[1]
        else:
            return True

    def profile_info(self):
        info = {
            'nick_name':self.nick_name,
            'joined_at':self.created_at,
            'zone':self.zone,
            'kundli_attributes':self.person_kundli_attributes,
            'profile_pics':self.profile_pics,
        }
        return info

    def full_profile_info(self,person):
        info = {
            'did':self.did,
            'nick_name':self.nick_name,
            'joined_at':self.created_at,
            'age':self.age,
            'year_of_birth':self.year_of_birth,
            'gender':self.gender,
            'profile_pics':self.profile_pics,
            'person_kundli_attributes':self.person_kundli_attributes,
            'interests':self.interests,
            'zone':self.zone,
            'city':self.city,
            'country':self.country,
            'marital_status':self.marital_status,
            'like_count':len(self.like.all()),
            'is_friend':True if person in self.friends.all() else False,
            'is_friend_requested_to':True if person in self.request.all() else False,
            'is_friend_requested_from':True if self in person.request.all() else False,
            'is_like_to':True if person in self.like.all() else False,
            'is_like_from':True if self in person.like.all() else False,
            'language_preference1':self.language_preference1,
            'language_preference2':self.language_preference2,
            'language_preference3':self.language_preference3,
        }
        return info


    def fetch_posts_new(self,page_number=1):
        offset = ((page_number or 1)*20) - 20
        # start = time.perf_counter()
        posts = self.cypher(
            f"""
            call{{
                match (self:Person{{did:$self_did}})
                with self
                match (p:Post)<-[:POST_FROM]-(n:Person)
                where size([x in self.interests where x in n.interests])>1 and n.did<>$self_did
                return {{post_from:{{did:n.did,nick_name:n.nick_name,zone:n.zone,joined_at:n.created_at,kundli_attributes:n.person_kundli_attributes,
                profile_pics:n.profile_pics,like_count:n.like_count,
                is_friend: exists((self)-[:FRIEND]-(n)),
                is_friend_requested_to: exists((self)-[:FRIEND_REQUEST]->(n)),
                is_friend_requested_from: exists((self)<-[:FRIEND_REQUEST]-(n)),
                is_like_to: exists((self)-[:likes]->(n)),
                is_like_from: exists((self)<-[:likes]-(n)) }},
                pid:p.pid,created_at:p.created_at,text:p.text,images:p.images,
                tags:[(p)-[:TAG]->(t:Tags)|t.tag_name],
                comments:[(p)<-[:COMMENT_TO]-(c:Comments)|c.comment],
                likes:p.likes}} as response_map order by p.created_at DESC skip $offset limit 20
            }} return collect(response_map)
            """,{"offset":offset,"self_did":self.did})[0][0][0]

        # end = time.perf_counter()
        # print("time:",end-start)
        return posts

    def match_person(self,page_number=1):
        # print(self.nick_name)
        offset = ((page_number or 1)*20) - 20
        # start = time.perf_counter()
        matches = self.cypher(
                f"""
                    call{{
                        match (self:Person{{did:$self_did}})
                        match (n:Person)
                        where n.zone=$self_zone and n.gender=$self_gender_preference and  n.did<>$self_did
                        with n,self,size((self)-[:MEMBER_OF]-(:Club)<-[:MEMBER_OF]-(n)) as common_c,
                        size([x in self.interests where x in n.interests]) as common_i,
                        [self.language_preference1=n.language_preference1,
                        self.language_preference2=n.language_preference2,
                        self.language_preference3=n.language_preference3] as l_list
                        return {{
                            did:n.did,
                            nick_name:n.nick_name,
                            joined_at:n.created_at,
                            year_of_birth:n.year_of_birth,
                            age:n.age,
                            gender:n.gender,
                            profile_pics:n.profile_pics,
                            person_kundli_attributes:n.person_kundli_attributes,
                            interests:n.interests,
                            zone:n.zone,
                            city:n.city,
                            country:n.country,
                            marital_status:n.marital_status,
                            like_count:n.likes,
                            language_preference1:n.language_preference1,
                            language_preference2:n.language_preference2,
                            language_preference3:n.language_preference3,
                            is_friend: exists((self)-[:FRIEND]-(n)),
                            is_friend_requested_to: exists((self)-[:FRIEND_REQUEST]->(n)),
                            is_friend_requested_from: exists((self)<-[:FRIEND_REQUEST]-(n)),
                            is_like_to: exists((self)-[:likes]->(n)),
                            is_like_from: exists((self)<-[:likes]-(n)),
                            common_clubs:common_c,
                            common_interests:common_i,
                            match_count:common_c*100 + common_i*10 + 100*size([x in l_list where x=true])
                        }} as match_map order by match_map['match_count'] DESC skip $offset limit 20
                    }}
                    return collect(match_map)

                """,{"self_did":self.did,"self_zone":self.zone,"self_gender_preference":self.gender_preference,"offset":offset})[0][0][0]

        # end = time.perf_counter()
        # print("time:",end-start)
        return matches


    def total_delete(self):
        try:
            response = self.cypher(
                f"""
                    match (self:Person{{did:$self_did}})-[:POST_FROM]->(post:Post)
                    optional match (post)<-[:COMMENT_TO]-(comment:Comments)
                    optional match (self)<-[:PAGE_OWNER]-(page:Page)
                    optional match (self)<-[:OWNER]-(club:Club)
                    detach delete self,post,comment,page,club
                    
                """,{"self_did":self.did})
            # self.cypher(f"match (p:Person{{email:'{self.email}'}})-[:POST_FROM]->(post:Post)-[rel:TAG]->(r) delete rel")
            # self.cypher(f"match (person:Person{{email:'{self.email}'}})-[*]-(r) detach delete r")
        except Exception:
            response = False
        else:
            return True
        return response

    def test(self):
        return self.serialize_relationships(self.posts.all())

class Tags(DjangoNode):
    tag_name = StringProperty(unique_index=True)
    tag_name_alias = StringProperty()

    tagFrom = RelationshipFrom('Post','TAG')

    class Meta:
        app_label = "neoUserModel"
        verbose_name_plural = "Tags"

    def __str__(self):
        return f"{self.tag_name}"

class Post(StructuredNode):
    pid = UniqueIdProperty()
    text = StringProperty()
    imageLink = ArrayProperty(StringProperty(),default=None)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")
    likes = IntegerProperty(defualt=0)

    liked_by = RelationshipFrom('Person','Like',model=LikeRel)
    comment = RelationshipFrom('Comments','COMMENT_TO') 
    postFrom = RelationshipFrom('Person','POST_FROM',cardinality=cardinality.One)
    postFromClub = RelationshipFrom('Club','POST_FROM_CLUB',cardinality=cardinality.One)
    postFromPage = RelationshipFrom('Page','POST_FROM_PAGE',cardinality=cardinality.One)
    tagTo = RelationshipTo('Tags','TAG')

    def post_from_info(self,person):
        postfrom = self.postFrom[0]
        info = {
            'did':postfrom.did,
            'nick_name':postfrom.nick_name,
            'joined_at':postfrom.created_at,
            'zone':postfrom.zone,
            'kundli_attributes':postfrom.person_kundli_attributes,
            'profile_pics':postfrom.profile_pics,
            'like_count':len(postfrom.like.all()),
            'is_friend':True if person in postfrom.friends.all() else False,
            'is_friend_requested_to':True if person in postfrom.request.all() else False,
            'is_friend_requested_from':True if postfrom in person.request.all() else False,
            'is_like_to': True if person in postfrom.like.all() else False,
            'is_like_from':True if postfrom in person.like.all() else False,
        }
        return info

    def tags(self):
        return self.cypher(
            f'''
                match (tag:Tags)<-[:TAG]-(post:Post{{pid:'{self.pid}'}}) return collect(tag.tag_name)
            '''
        )[0][0][0]

    def comments(self):
        return self.cypher(
            f'''
                match (comment:Comments)-[:COMMENT_TO]->(p:Post{{pid:'{self.pid}'}}) return collect(comment.comment)
            '''
        )[0][0][0]


    def post_info(self,person):
        from_object = self.post_from_info(person)
        tags = self.tags()
        comments = self.comments()
        info = {
            'post_from':from_object,
            'pid':self.pid,
            'created_at':self.created_at,
            'text':self.text,
            'images':self.imageLink,
            'tags':tags,
            'likes':self.likes,
            'comments':comments,
        }

        return info


class Comments(StructuredNode):
    comment = StringProperty(default=None)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")

    commentFrom = RelationshipFrom('Person','COMMENT_FROM')
    commentTo = RelationshipTo('Post','COMMENT_TO')


class Transaction_Rel(StructuredRel):
    transaction_id = StringProperty()
    requested_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")
    accepted_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")


class Club(DjangoNode):
    club_id = UniqueIdProperty()
    club_name = StringProperty(required=True)
    description = StringProperty(default=None,)
    profile_image = StringProperty(default=None)
    cover_image = StringProperty(default=None)
    category = StringProperty(required=True)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")

    #relations
    posts = RelationshipTo('Post','POST_FROM_CLUB',)
    owner = Relationship('Person','OWNER',cardinality=cardinality.One)
    members = RelationshipFrom('Person','MEMBER_OF',model=Transaction_Rel)
    request_membership = RelationshipFrom('Person','REQUEST_MEMBERSHIP',model=Transaction_Rel)

    class Meta:
        app_label = "neoUserModel"

    def __str__(self):
        return f"{self.club_name}-{self.club_id}-{self.owner[0].did}"

class Page(DjangoNode):
    page_id = UniqueIdProperty()
    page_name = StringProperty(required=True)
    description = StringProperty(default=None)
    profile_image = StringProperty(default=None)
    cover_image = StringProperty(default=None)
    likes = IntegerProperty(default=0)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")

    # relationships
    posts = RelationshipTo('Post','POST_FROM_PAGE')
    owner = Relationship('Person','PAGE_OWNER',cardinality=cardinality.One)
    liked_by = RelationshipFrom('Person','Like',model=LikeRel)

    class Meta:
        app_label="neoUserModel"

    def __str__(self):
        return f"{self.page_name}-{self.page_id}-{self.owner[0].did}"

    def page_from_info(self,person):
        owner = self.owner[0]
        info = {
            'did':owner.did,
            'nick_name':owner.nick_name,
            'joined_at':owner.created_at,
            'kundli_attributes':owner.person_kundli_attributes,
            'zone':owner.zone,
            'like_count':len(owner.like.all()),
            'profile_pics':owner.profile_pics,
            'is_friend':True if person in owner.friends.all() else False,
            'is_friend_requested_to':True if person in owner.request.all() else False,
            'is_friend_requested_from':True if owner in person.request.all() else False,
            'is_like_to': True if person in owner.like.all() else False,
            'is_like_from':True if owner in person.like.all() else False,
        }
        return info

    def page_info(self,person):
        owner_info = self.page_from_info(person)
        info = {
            'page_id':self.page_id,
            'page_name':self.page_name,
            'description':self.description,
            'profile_image':self.profile_image,
            'cover_image':self.cover_image,
            'created_at':self.created_at,
            'like_count':len(self.liked_by.all()),
            'is_like_to':True if person in self.liked_by.all() else False,
            'owner':owner_info,
        }
        return info


class Channel(StructuredNode):
    room_id = UniqueIdProperty(primary_key=True)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")
    # created_at = DateTimeProperty(default_now=True)
    is_created = BooleanProperty(default=True)

    messages = RelationshipFrom('Message','CHANNEL')
    members = RelationshipFrom('Person','CHANNEL_MEMBER')

    def __str__(self):
        return f"{self.room_id}"




class Message(StructuredNode):
    message_id = UniqueIdProperty(primary_key=True)
    text = StringProperty(required=True)
    created_at = DateTimeFormatProperty(default_now=True,format="%Y-%m-%d %H:%M:%S")

    message_from = StringProperty()
    message_to = StringProperty()

    channel = RelationshipTo('Channel','CHANNEL')

    def __str__(self):
        return f"{self.text}-{self.message_id}"