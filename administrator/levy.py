from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from administrator.models import Levy, SchoolProfile
from administrator.serializers import LeviesSerializer
from django.shortcuts import get_object_or_404, render



def is_admin(user):
    return getattr(user, 'is_admin', False)

def is_manager(user):
    return getattr(user, 'is_manager', False)



class LeviesListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Levy"])
    def get(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        levies = Levy.objects.filter(school=school)
        serializer = LeviesSerializer(levies, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(tags=["Levy"])
    def post(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        name = request.data.get("name", "").strip()

        # Check for duplicate name in the same school
        if Levy.objects.filter(school=school, name__iexact=name).exists():
            return Response(
                {"error": "Levy with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new subject
        levy = Levy.objects.create(school=school, name=name)
        serializer = LeviesSerializer(levy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class LevyUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Levy"])
    def put(self, request, levy_id):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        levy = get_object_or_404(Levy, id=levy_id)
        serializer = LeviesSerializer(levy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Levy"])
    def delete(self, request, levy_id):
        levy = get_object_or_404(Levy, id=levy_id)
        levy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)