from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from administrator.models import AcademicSession, Parent, SchoolProfile
from administrator.parent_manager import ParentAccessCodeAuthentication
from .parent_serializers import ParentCreateSerializer, ParentListSerializer, ParentLoginSerializer, ParentUpdateSerializer, StudentNestedSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


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
