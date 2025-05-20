from rest_framework import serializers
from rest_framework.exceptions import ParseError

from .models import User



class RegUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email','phone','password', "is_admin","is_manager"]
        
    def validate_password(self, value):
        if len(value) < 8:
            raise ParseError("Password must be at least 8 characters long.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create(
            **validated_data,
            is_admin=True
        )        
        
        return user
    
    

class UserVerificationSerializer(serializers.Serializer):
    token = serializers.IntegerField(required = True)
    
    def validate_token(self, value):
        if not (100000 <= value <= 999999):
            raise ParseError("Token must be exactly 6 digits long.")
        return value
    
    

class ResendVerificationTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)



class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    
    def validate_password(self, value):
        if len(value) < 8:
            raise ParseError("Password must be at least 8 characters long.")
        return value
    
    
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    
    
class ForgetPasswordVerificationTokenSerializer(serializers.Serializer):
    token = serializers.IntegerField(required=True)
    password = serializers.CharField(required=True)
    
    def validate_password(self, value):
        if len(value) < 8:
            raise ParseError("Password must be at least 8 characters long.")
        return value
    
    def validate_token(self, value):
        if not (100000 <= value <= 999999):
            raise ParseError("Token must be exactly 6 digits long.")
        return value
    
    
    
class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    password1 = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)
    
    def validate(self, data):
        password = data.get("password")
        password1 = data.get("password1")
        password2 = data.get("password2")

        if len(password) < 8:
            raise ParseError("Current password must be at least 8 characters long.")

        if len(password1) < 8:
            raise ParseError("New password must be at least 8 characters long.")

        if password1 != password2:
            raise ParseError("New passwords do not match.")

        if password == password1:
            raise ParseError("New password must be different from the current password.")

        return data
    
    
    
class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']
        
    def get_profile_picture(self, obj):
        request = self.context.get("request")
        if obj.profile_picture and hasattr(obj.profile_picture, "url"):
            return request.build_absolute_uri(obj.profile_picture.url)
        return None
        
        

