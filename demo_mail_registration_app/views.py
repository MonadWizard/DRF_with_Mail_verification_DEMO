from django.http import HttpResponse

from rest_framework import generics, status, views
from rest_framework.response import Response

# from rest_framework_simplejwt.tokens import 
from .models import User
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt, datetime
from django.conf import settings
from django.db import connection


# Create your views here.


class RegisterView(generics.GenericAPIView):
    
    def post(self, request):
        data = request.data
        username = data['username']
        email = data['email']
        password = data['password']

# Token passing
        payload = {
            'email': email,
            'username': username,
            'password': password,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=100, seconds=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        absurl = 'http://'+current_site+relativeLink+"?token="+str(token)
        
        email_body = 'Hi '+username + \
            ' Use the link below to verify your email \n' + absurl
        
        data = {'email_body': email_body, 'to_email': email,
                'email_subject': 'Verify your email'}

        Util.send_email(data)

        return Response(data, status=status.HTTP_201_CREATED)



class VerifyEmail(views.APIView):

    def get(self, request):
        token = request.GET.get('token')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # print('payload:::: ', payload)

            user_register = User.objects.create_user(payload['username'], payload['email'], payload['password'])
            user_register.save()

            html = "<html><body>Verification Success. It's time for login</body></html>"
            return HttpResponse(html)
            # return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError as identifier:
            html = "<html><body>Activation Expired.</body></html>"
            return HttpResponse(html)
            # return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            html = "<html><body>Invalid token.</body></html>"
            return HttpResponse(html)
            # return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

