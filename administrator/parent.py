from datetime import timedelta
import random
import secrets
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from administrator.models import AcademicSession, Parent, SchoolProfile
from administrator.parent_manager import ParentAccessCodeAuthentication
from authentication.serializers import ChangePasswordSerializer, ForgetPasswordSerializer
from authentication.swagger import TaggedAutoSchema
from .parent_serializers import ParentCreateSerializer, ParentListSerializer, ParentLoginSerializer, ParentUpdateSerializer, StudentNestedSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from datetime import timedelta
import secrets

def is_admin(user):
    return getattr(user, 'is_admin', False)


class ParentCreateListsView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParentListSerializer
    def post(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        
        school = SchoolProfile.objects.filter(user=self.request.user).first()
        serializer = ParentCreateSerializer(data=request.data)
        if serializer.is_valid():
            parent = serializer.save(school=school)
            return Response({
                "message": "Parent created successfully.",
            }, status=status.HTTP_201_CREATED)
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        
        school = SchoolProfile.objects.filter(user=self.request.user).first()
        queryset = Parent.objects.filter(school = school)
        return queryset


class ParentLoginView(APIView):
    def post(self, request):
        serializer = ParentLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.core.cache import cache
from django.contrib.auth.hashers import make_password


class ParentForgetPasswordView(generics.GenericAPIView):
    serializer_class = ForgetPasswordSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        
        try:
            parent = Parent.objects.get(email=email)
            
            # Generate a random token and store it temporarily
            token = secrets.token_urlsafe(32)
            expiry = timezone.now() + timedelta(minutes=10)
            
            # Store token in cache
            cache_key = f'password_reset_{parent.id}'
            cache.set(cache_key, {
                'token': token,
                'expiry': expiry.isoformat()
            }, timeout=600)
            
            uidb64 = urlsafe_base64_encode(force_bytes(parent.id))
            verification_link = request.build_absolute_uri(
                reverse('parent-verify-email', kwargs={'uidb64': uidb64, 'token': token})
            )
            
            send_mail(
                'Password Reset Link',
                f'Click this link to reset your password: {verification_link}\n'
                f'This link expires in 10 minutes.',
                settings.EMAIL_HOST_USER,
                [parent.email],
                fail_silently=False,
            )
            
            return Response({"message": "Password reset link sent to your email"}, status=status.HTTP_200_OK)
            
        except Parent.DoesNotExist:
            return Response({"error": "Parent with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class ParentPasswordResetVerifyView(generics.GenericAPIView):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            parent = Parent.objects.get(id=uid)
            
            # Retrieve from cache
            cache_key = f'password_reset_{parent.id}'
            cached_data = cache.get(cache_key)
            
            if not cached_data or cached_data['token'] != token:
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
                
            expiry = timezone.datetime.fromisoformat(cached_data['expiry'])
            if timezone.now() > expiry:
                return Response({"error": "Token has expired"}, status=status.HTTP_400_BAD_REQUEST)
                
            # Token is valid - show password reset form
            default_password = secrets.token_urlsafe(9)
            parent.password = make_password(str(default_password))
            parent.save()
            cache.delete(cache_key)
            
            send_mail(
                'Default Password',
                f'Your default password: {default_password}\n',
                settings.EMAIL_HOST_USER,
                [parent.email],
                fail_silently=False,
            )
            
            return Response({"message": "Password updated successfully, check mail for default password"}, status=status.HTTP_200_OK)
            
            
        except (TypeError, ValueError, OverflowError, Parent.DoesNotExist):
            return Response({"error": "Invalid Parent"}, status=status.HTTP_400_BAD_REQUEST)


class ParentChangePasswordView(generics.GenericAPIView):
    swagger_schema = TaggedAutoSchema
    serializer_class = ChangePasswordSerializer
    authentication_classes = [ParentAccessCodeAuthentication]
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            password1 = serializer.validated_data['password1']
            password2 = serializer.validated_data['password2']
            
            if len(password) < 8 or len(password1) < 8 or len(password2) < 8:
                return Response({'error': 'Password must be at least 8 characters long.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure new password matches confirmation
            if password1 != password2:
                return Response({'error': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)
            
            parent = request.user
            if not parent.check_password(password):
                return Response({"error": "Old Password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            parent.password = make_password(password1)
            parent.save()
                
            
            return Response({'message': 'Password Changed'}, status=status.HTTP_200_OK)
    
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ParentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParentUpdateSerializer
    queryset = Parent.objects.all()

    def patch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")

        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")

        return self.update(request, *args, **kwargs)
    
    
    
class ParentDashboardView(APIView):
    authentication_classes = [ParentAccessCodeAuthentication]
    def get(self, request):
        parent = request.user
        print(parent)
        students = parent.student.all()
        session = AcademicSession.objects.filter(school__school_name=parent.school.school_name).count()
        school = SchoolProfile.objects.filter(school_name=parent.school.school_name).first()
        serializer = StudentNestedSerializer(students, many=True)
        return Response({
            "students":serializer.data,
            "students_count": len(students),
            "sessions": session,
            "school_name":school.school_name,
            "school_location" : school.school_address or "not set"
            }, status=status.HTTP_200_OK) 
