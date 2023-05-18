"""DropDAPI URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from authUser.views import *
from rest_framework.authtoken.views import obtain_auth_token
from neoUserModel.views import *

admin.site.site_header = "DropD Admin"
admin.site.site_title = "DropD Admin"
admin.site.index_title = "Welcome to DropD Admin"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/signup/',SignUp.as_view(),name='signup'),
    path('v1/signup-verification/',signupVerification,name="registration-verification"),
    path('v1/register-email/',RegisterEmail,name="register-email"),
    path('v1/email-verification/',emailVerification,name="verify-email"),
    path('v1/login/',Login,name="login"),
    path('v1/login-otp-verification/',LoginOtpVerification,name="confim-login-otp"),
    path('v1/update-nickname/',UpdateNickname,name="update-nick-name"),
    path('v1/check-nickname/',checkNickname,name="check-nick-name"),
    path('v1/update-profile-images/',UpdateProfileImages,name="profilepic-upload"),
    path('v1/view-profile/',viewProfile,name="profile-view"),
    path('v1/view-user-profile/<str:did>/',viewUserProfile,name="profile-user-view"),
    path('v1/update-profile/',UpdateProfile,name='complete-profile'),
    path('v1/posts/',include('neoUserModel.urls',namespace='neoUserModel')),
    path('v1/interests/',get_interests,name="get-interests"),
    path('v1/timeline/p/<int:page_number>/',timeline,name="timeline"),
    path('v1/timeline/',timelineTemp,name="timeline"),
    path('v1/view-match/p/<int:page_number>/',viewMatch,name="view-match"),

    path('v1/view-match/',viewMatchOld,name="view-match"),

    path('v1/view-match/count/',viewMatchCount,name="view-match-count"),

    path('v1/create-club/',createClub,name="crerat club"),
    path('v1/update-club/',updateClub,name="update-club"),
    path('v1/view-club/<str:club_id>/',viewClub,name="get-club"),
    path('v1/delete-club/',deleteClub,name="delete-club"),
    path('v1/join-club/',joinClub,name="join-club"),
    path('v1/validate-transaction/',validateTransaction,name="validate-transaction"),
    path('v1/club-member-list/<str:club_id>/',clubMembers,name="club-members"),
    path('v1/all-club-list/',allClubListOld,name="all-club-list"),

    path('v1/all-club-list/p/<int:page_number>/',allClubList,name="all-club-list"),

    path('v1/my-club-list/',myClubListOld,name="my-club-list"),

    path('v1/my-club-list/p/<int:page_number>/',myClubList,name="my-club-list"),

    path('v1/like-person/',personLike,name="person-like"),
    path('v1/create-page/',createPage,name="create-page"),
    path('v1/update-page/',updatePage,name="update-page"),
    path('v1/view-page/<str:page_id>/',viewPage,name="get-page"),
    path('v1/delete-page/',deletePage,name="delete-page"),
    path('v1/like-page/',likePage,name="like-page"),

    path('v1/all-page-list/',allPageListOld,name="all-page-list"),

    path('v1/all-page-list/p/<int:page_number>/',allPageList,name="all-page-list"),

    path('v1/my-page-list/',myPageListOld,name="my-page-list"),

    path('v1/my-page-list/p/<int:page_number>/',myPageList,name="my-page-list"),

    path('v1/friend-request/',friendRequest,name="request-friend"),
    path('v1/friend-request-list/',friendRequestList,name="request-list"),
    path('v1/friend-request-sent-list/',friendRequestSentList,name="request-list"),
    path('v1/friend-request-accept/',friendRequestAccept,name="request-accept"),
    path('v1/friend-request-reject/',friendRequestReject,name="request-reject"),
    path('v1/friend-list/',friendListOld,name="friend-list"),

    path('v1/friend-list/<int:page_number>/',friendList,name="friend-list"),

    path('v1/make-friend/',make_friend,name="make_friend"),
    # path('v1/login-view/',login_view,name="login-view"),
    # path('v1/<str:uid>/chats/',chats,name="chat-list"),
    # path('v1/chat/friend/<str:nick_name>/<int:did>/<str:room_code>/',chat_room,name="chat-room"),



    path('v1/get-json-web-token/',get_jwt,name="get-token"),
    # path('test/',test_api,name="test-api"),

]
