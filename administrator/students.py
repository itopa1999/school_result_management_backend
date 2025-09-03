import os
from django.conf import settings
from django.http import FileResponse
from rest_framework.exceptions import ParseError
import pandas as pd
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from administrator.models import AcademicSession, ClassLevel, SchoolProfile, Student, StudentEnrollment
from rest_framework.permissions import IsAuthenticated

from administrator.serializers import StudentUploadPreviewSerializer


class DownloadTemplateView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Student"])
    def get(self, request, *args, **kwargs):
        template_filename = "upload_students_template.xlsx"
        file_path = os.path.join(settings.MEDIA_ROOT, "Documents", template_filename)

        if not os.path.exists(file_path):
            raise ParseError("Template file not found.")

        # Return the file as a download response
        response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{template_filename}"'
        return response
    

class PreviewStudentsUploadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = StudentUploadPreviewSerializer
    @swagger_auto_schema(tags=["Student"])
    def post(self, request):
        file = request.FILES.get('file')
        class_level_id = request.data.get('classLevel')

        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        if not class_level_id:
            return Response({'error': 'Class Level not selected.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({'error': f'Invalid Excel file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        required_columns = ['Name', 'Other info']
        if not all(col in df.columns for col in required_columns):
            return Response({
                'error': f'Missing required columns. Required: {required_columns}'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        class_level = ClassLevel.objects.filter(school=school, id=class_level_id).first()

        if not class_level:
            return Response({'error': 'Invalid class level selected.'}, status=status.HTTP_400_BAD_REQUEST)

        cleaned_data = []

        for _, row in df.iterrows():
            name = str(row['Name']).strip() if not pd.isna(row['Name']) else ''
            other_info = str(row['Other info']).strip() if not pd.isna(row['Other info']) else ''

            if name and other_info:
                cleaned_data.append({
                    'name': name,
                    'other_info': other_info,
                })

        return Response({
            'class_level': class_level.name,
            'class_level_id': class_level.id,
            'students': cleaned_data,
            'total_valid': len(cleaned_data)
        }, status=status.HTTP_200_OK)  

class UploadStudentsView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Student"])
    def post(self, request):
        students = request.data.get('students', [])
        class_level_id = request.data.get('class_level_id')

        if not students:
            return Response({'error': 'No students provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if not class_level_id:
            return Response({'error': 'Class Level ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        

        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        
        session = AcademicSession.objects.filter(school = school, is_current=True).first()
        if not session:
            return Response({"error": "session not set"}, status=404)
        
        class_level = ClassLevel.objects.filter(school=school, id=class_level_id).first()

        if not class_level:
            return Response({'error': 'Invalid class level selected.'}, status=status.HTTP_400_BAD_REQUEST)

        updated_rows = 0
        skipped_rows = 0
        created_students = 0
        for student in students:
            name = student.get('name', '').strip()
            other_info = student.get('other_info', '').strip()

            if not name or not other_info:
                skipped_rows += 1
                continue
            

            existingStudent = Student.objects.filter(name__iexact=name.capitalize(), school=school).first()
            if existingStudent:
                existingStudent.other_info = other_info
                existingStudent.save()
                updated_rows += 1
                
                existingStudentEnroll = StudentEnrollment.objects.filter(student = existingStudent, school=school, session = session).first()
                if not existingStudentEnroll:
                    StudentEnrollment.objects.create(
                        student=existingStudent,
                        class_level=class_level,
                        session=session,
                        school=school
                    )
            else:
                new_student = Student.objects.create(
                    school=school,
                    name=name,
                    other_info=other_info
                )
                created_students += 1
                
                existingStudentEnroll = StudentEnrollment.objects.filter(student = new_student, school=school, session = session).first()
                if not existingStudentEnroll:
                    StudentEnrollment.objects.create(
                        student=new_student,
                        class_level=class_level,
                        session=session,
                        school=school
                    )

        return Response({
            'message': 'Student upload successful.',
            'saved': created_students,
            'updated': updated_rows,
            'skipped': skipped_rows
        }, status=status.HTTP_201_CREATED)