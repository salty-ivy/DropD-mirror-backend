from django.shortcuts import render

# Create your views here.

from authUser.models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view , authentication_classes ,permission_classes
from rest_framework.authentication import TokenAuthentication
from authUser.serializers import *
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from neoUserModel.models import *
from datetime import datetime
from authUser.helper import handle_post_upload,delete_media_files,custom_file_validator


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def CreatePost(request):
	person = Person.nodes.get(did=request.user.id)
	if request.FILES:
		media = request.FILES
		if not custom_file_validator(media):
			return Response({
					'status':'error',
					'message':'Invalid file type'
				},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		media = None
	text = request.data.get('text')
	club_id = request.data.get('club_id')
	page_id = request.data.get('page_id')

	try:
		tags = request.data.getlist('tags')
	except:
		tags = None
	else:
		for tag in tags:
			if not tag.startswith('#'):
				return Response({
						'status':'error',
						'message':'Invalid tag.',
					},status=status.HTTP_406_NOT_ACCEPTABLE)
			if " " in tag:
				return Response({
						'status':'error',
						'message':'A tag can not contain spaces.'
					},status=status.HTTP_406_NOT_ACCEPTABLE)

	if text==None and media==None:
		return Response({
				'status':'error',
				'message':'Empty post is not allowed.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		post = Post().save()
		if text is not None:
			post.text=text
		if media is not None:
			urls = handle_post_upload(media,post.id)
			post.imageLink = urls
		post.likes = 0
		# post.created_at = datetime.now()
		# post.save()
		post.postFrom.connect(person)
		post.save()
		if club_id is not None:
			try:
				club=Club.nodes.get(club_id=club_id)
			except:
				return Response({
						'status':'error',
						'message':'Invalid club ID',
					},status=status.HTTP_404_NOT_FOUND)
			else:
				if club in person.clubs.all():
					post.postFromClub.connect(club)
					post.save()
				else:
					return Response({
							'status':'error',
							'message':'You can not post for this club since you are not a member of this club'
						},status=status.HTTP_406_NOT_ACCEPTABLE)
		elif page_id is not None:
			try:
				page = Page.nodes.get(page_id=page_id)
			except:
				return Response({
						'status':'error',
						'message':'Invalid page ID'
					},status=status.HTTP_404_NOT_FOUND)
			else:
				if page.owner[0] == person:
					post.postFromPage.connect(page)
					post.save()
				else:
					return Response({
							'status':'error',
							'message':'You can not create post for this page since you are not the Owner of this page.'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

		if tags is not None:
			for tag in tags:
				try:
					tagNode = Tags.nodes.get(tag_name_alias=tag.lower())
				except:
					tagNode = None
				if tagNode is not None:
					post.tagTo.connect(tagNode)
					post.save()
				else:
					tagNode = Tags(tag_name=tag,tag_name_alias=tag.lower())
					tagNode.save()
					post.tagTo.connect(tagNode)
					post.save()
		if post.postFrom.is_connected(person):
			return Response({
				'status':'success',
				'message':'posted',
				'post_data':f'{post.pid}-{person.nick_name}.',
			},status=status.HTTP_201_CREATED)

		return Response({
				'status':'error',
				'message':'Post connection error.'
			})


@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated,])
def viewPost(request,pid):
	try:
		post = Post.nodes.get(pid=pid)
	except:
		return Response({
				'status':'success',
				'message':'Post does not exists.'
			},status=status.HTTP_404_NOT_FOUND)
	else:
		context = {}
		context['status']='success'
		context['message']='post loaded.'
		tags = []
		for tag in post.tagTo.all():
			tags.append(tag.tag_name)
		comments = []
		for comment in post.comment.all():
			commentFrom = comment.commentFrom.all()[0]
			comment_object = {
				'comment_id':comment.id,
				'comment':comment.comment,
				'comment_date':comment.created_at,
				'comment_from':{
					'nick_name':commentFrom.nick_name,
					'joined_at':commentFrom.created_at,
					'profile_pics':commentFrom.profile_pics,
				}
			}
			comments.append(comment_object)

		postfrom = post.postFrom.all()[0]
		person = Person.nodes.get(did=request.user.id)
		from_object = {
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
			'is_like_to':True if person in postfrom.like.all() else False,
			'is_like_from':True if postfrom in person.like.all() else False,
		}
		context['post'] = {
				'post_from':from_object,
				'pid':post.pid,
				'text':post.text,
				'images':post.imageLink,
				'tags':tags,
				'like_count':post.likes,
				'comments':comments,
		}

		return Response(context,status=status.HTTP_200_OK)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def updatePost(request):
	if not request.data:
		return Response({
				'status':'error',
				'message':'Fields are empty'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	pid = request.data.get('post_id')
	try:
		post = Post.nodes.get(pid=pid)
	except:
		return Response({
				'status':'error',
				'message':'Post not found,invalid post id'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if request.user.id == post.postFrom.all()[0].did:
			text = request.data.get('text')
			media = request.FILES
			tags = request.data.getlist('tags')

			if tags is not None:
				for tag in post.tagTo.all():
					post.tagTo.disconnect(tag)
				for tag in tags:
					if tag[0]!="#":
						return Response({
								'status':'error',
								'message':'Invalid tag.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					else:
						try:
							tagNode = Tags.nodes.get(tag_name_alias=tag.lower())
							if not post.tagTo.is_connected(tagNode):
								post.tagTo.connect(tagNode)
								post.save()

						except:
							tagNode = Tags(tag_name=tag,tag_name_alias=tag.lower()).save()
							post.tagTo.connect(tagNode)
							post.save()

			if text is not None:
				post.text = text
				post.save()

			if media is not None:
				if not custom_file_validator(media):
					return Response({
							'status':'error',
							'message':'Invalid file type.'
						},status=status.HTTP_406_NOT_ACCEPTABLE)
				if delete_media_files(post.imageLink):
					post.imageLink = handle_post_upload(media,post.pid)
					post.save()
			return Response({
					'status':'success',
					'message':'Post updated successfully.'
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':'Only the Owner of this post cant make changes.'
				},status=status.HTTP_406_NOT_ACCEPTABLE)

#no status
@api_view(['POST'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated,])
def getUserPosts(request):
	did = request.data.get('did')
	if did:
		try:
			person = Person.nodes.get(did=did)
		except:
			return Response({
					'status':'error',
					'message':'User not found.'
				},status=status.HTTP_404_NOT_FOUND)
		else:
			self_person = Person.nodes.get(did=request.user.id)
			from_object = {
				'did':person.did,
				'nick_name':person.nick_name,
				'joined_at': person.created_at,
				'kundli_attributes':person.person_kundli_attributes,
				'profile_pics':person.profile_pics,
				'like_count':len(person.like.all()),
				'is_friend':True if self_person in person.friends.all() else False,
				'is_friend_requested_to':True if self_person in person.request.all() else False,
				'is_friend_requested_from':True if person in self_person.request.all() else False,
				'is_friend_requested_to':True if self_person in person.like.all() else False, 

			}

	else:
		try:
			person = Person.nodes.get(did=request.user.id)
		except:
			return Response({
					'status':'error',
					'message':'User not found.'
				},status=status.HTTP_404_NOT_FOUND)
		else:
			from_object = {
				'did':person.did,
				'nick_name':person.nick_name,
				'joined_at': person.created_at,
				'kundli_attributes':person.person_kundli_attributes,
				'like_count':len(person.like.all()),				
				'profile_pics':person.profile_pics,
			}


	context = {}
	context['status']=''
	context['message']=''
	context['post_from']=None
	context['posts']=[]


	context['post_from']=from_object
	for post in person.posts.all():
		context['posts'].append({
			'pid':post.pid,
			'text' : post.text,
			'media_links' : post.imageLink,
			'tags':[tag.tag_name for tag in post.tagTo.all()],
			'like_count':post.likes,
		})
	context['status'] = "success"
	context['message']="Posts loaded."
	return Response(context,status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def likePost(request):
	person = Person.nodes.get(did=request.user.id)
	pid = request.data.get('post_id')
	if pid is None:
		return Response({
				'status':'error',
				'message':'Invalid post ID.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	try:
		post = Post.nodes.get(pid=pid)
	except:
		return Response({
				'status':'error',
				'message':'Post does not exists'
			},status=status.HTTP_404_NOT_FOUND)

	if post.liked_by.is_connected(person):
		current_likes = int(post.likes)
		post.likes = current_likes - 1
		post.liked_by.disconnect(person)
		post.save()
		return Response({
				'status':'success',
				'message':f'{person.nick_name} disliked your post.',
				'like_count':post.likes
			},status=status.HTTP_200_OK)
	else:
		relation = post.liked_by.connect(person)
		relation.liked_at = datetime.now()
		relation.save()
		current_likes = int(post.likes)
		post.likes = current_likes + 1
		post.save()
		return Response({
				'status':'success',
				'message':f'{person.nick_name} liked your post.',
				'like_count':post.likes
			},status=status.HTTP_200_OK)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def commentOnPost(request):
	person = Person.nodes.get(did=request.user.id)
	pid = request.data.get('post_id') if request.data.get('post_id') else None

	if pid is None:
		return Response({
				'status':'error',
				'message':'Post id invalid.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	try:
		post = Post.nodes.get(pid=pid)
	except:
		return Response({
				'status':'error',
				'message':'Post does not exits.',
			},status=status.HTTP_404_NOT_FOUND)
		
	comment = request.data.get('comment')
	if comment:
		comment = Comments(comment = comment)
		comment.created_at = datetime.now()
		comment.save()
		comment.commentFrom.connect(person)
		comment.commentTo.connect(post)
		comment.save()
		return Response({
				'status':'success',
				'message':f'Comment from {person.nick_name}.',
			},status=status.HTTP_200_OK)

	return Response({
		'status':'error',
		'message':'Can not make empty comment.',
	},status=status.HTTP_406_NOT_ACCEPTABLE)