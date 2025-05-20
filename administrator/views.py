from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render

# Create your views here.


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from administrator.serializers import AcademicSessionSerializer, ClassLevelSerializer, DashboardSerializer, MainInfoSerializer, ResultSerializer, StudentSerializer, TermTotalMarkSerializer
from .models import AcademicSession, ClassLevel, Result, Student, Term, SchoolProfile, TermTotalMark
from rest_framework.permissions import IsAuthenticated



class MainInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the school for the current user
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        
        if not school:
            return Response({"detail": "No school profile associated with user."}, status=404)

        current_session = AcademicSession.objects.filter(school=school, is_current=True).first()
        current_term = Term.objects.filter(session=current_session, is_current=True).first()

        # Example fallback values
        session_id = current_session.id if current_session else 0
        term_id = current_term.id if current_term else 0

        data = {
            "current_session_id": session_id,
            "current_term_id": term_id,
            "school_name": school.school_name,
        }

        serializer = MainInfoSerializer(data)
        return Response(serializer.data)
    

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the school for the current user
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        
        if not school:
            return Response({"detail": "No school profile associated with user."}, status=404)

        current_session = AcademicSession.objects.filter(school=school, is_current=True).first()
        current_term = Term.objects.filter(session=current_session, is_current=True).first()
        active_classes = ClassLevel.objects.filter(school=school).count()

        # Example fallback values
        session_name = current_session.name if current_session else "Not Set"
        term_name = current_term.name if current_term else "Not Set"

        data = {
            "current_session": session_name,
            "current_term": term_name,
            "active_classes": active_classes,
            "school_info": {
                "school_name": school.school_name,
                "location": school.school_address or "Not Set",
                "total_students": 1250 
            }
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)
    
    

class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        session_name = request.data.get("session_name")
        is_current_session = request.data.get("is_current", False)
        user = request.user
        if not session_name:
            return Response({"error": "session_name and school_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            school = SchoolProfile.objects.filter(user=user).first()
        except SchoolProfile.DoesNotExist:
            return Response({"error": "School not found."}, status=status.HTTP_404_NOT_FOUND)

        if AcademicSession.objects.filter(school=school, name=session_name).exists():
            return Response({"error": f"Session '{session_name}' already exists for this school."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Deactivate previous current session/terms if this one is set as current
            if is_current_session:
                AcademicSession.objects.filter(school=school, is_current=True).update(is_current=False)
                Term.objects.filter(session__school=school, is_current=True).update(is_current=False)

            # Create session
            new_session = AcademicSession.objects.create(
                school=school,
                name=session_name,
                is_current=is_current_session
            )

            # Create terms
            term_names = ["First Term", "Second Term", "Third Term"]
            for term_name in term_names:
                Term.objects.create(
                    session=new_session,
                    name=term_name
                )

        return Response({"message": f"Session '{session_name}' created with 3 terms."},
                        status=status.HTTP_201_CREATED)


class AcademicSessionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        if not school:
            return Response([])

        sessions = AcademicSession.objects.filter(school=school)
        serializer = AcademicSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    
class ToggleAcademicSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = AcademicSession.objects.get(pk=pk)
        except AcademicSession.DoesNotExist:
            return Response({'error': 'Academic session not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Deactivate all sessions and all their terms
        AcademicSession.objects.all().update(is_current=False)
        Term.objects.all().update(is_current=False)

        # Activate selected session
        session.is_current = True
        session.save()

        return Response({'message': 'Academic session activated successfully.'}, status=status.HTTP_200_OK)


class ToggleTermAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            term = Term.objects.select_related('session').get(pk=pk)
        except Term.DoesNotExist:
            return Response({'error': 'Term not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the session of the term is currently active
        if not term.session.is_current:
            return Response({'error': 'Cannot activate term. Its session is not active.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deactivate all terms under the same session
        Term.objects.filter(session=term.session).update(is_current=False)

        # Activate this term
        term.is_current = True
        term.save()

        return Response({'message': 'Term activated successfully.'}, status=status.HTTP_200_OK)
    
    
    
class ClassLevelListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        class_levels = ClassLevel.objects.filter(school=school)
        serializer = ClassLevelSerializer(class_levels, many=True)
        return Response(serializer.data)

class ClassLevelStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, class_level_id):
        class_level = get_object_or_404(ClassLevel, id=class_level_id)
        students = Student.objects.filter(class_level=class_level)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

class StudentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    def put(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = StudentSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


import os
from rest_framework.exceptions import ParseError
import pandas as pd

class DownloadTemplateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        template_filename = "upload_students_template.xlsx"
        file_path = os.path.join(settings.MEDIA_ROOT, "Documents", template_filename)

        if not os.path.exists(file_path):
            raise ParseError("Template file not found.")

        # Return the file as a download response
        response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{template_filename}"'
        return response
    
    

class UploadStudentsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
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
            return Response({'error': f'Missing required columns. Required: {required_columns}'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        classLevel = ClassLevel.objects.filter(school=school, id=class_level_id).first()
        if not classLevel:
            return Response({'error': 'Invalid class level selected.'}, status=status.HTTP_400_BAD_REQUEST)
        students_to_create = []
        skipped_rows = 0
        updated_rows = 0
        total_rows = len(df)

        for _, row in df.iterrows():
            # Check for empty required fields
            if any(pd.isna(row[col]) or str(row[col]).strip() == '' for col in required_columns):
                skipped_rows += 1
                continue

            try:
                student = Student.objects.filter(name__iexact=row['Name'].strip(), class_level=classLevel).first()
                if student:
                    # Update existing student
                    student.title = row['Other info']
                    student.save()
                    updated_rows += 1
                    continue
                product = Student(
                    class_level = classLevel,
                    name=row['Name'],
                    other_info=row['Other info'],
                )
                students_to_create.append(product)
                
            except Exception:
                print("hi")
                skipped_rows += 1

        Student.objects.bulk_create(students_to_create)
        saved_rows = len(students_to_create)

        return Response({
            'message': 'Students upload completed.',
            'total_collected': total_rows,
            'total_saved': saved_rows,
            'total_skipped': skipped_rows,
            "updated_rows": updated_rows
        }, status=status.HTTP_201_CREATED)



class ResultListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, student_id, term_id, session_id):
        # Filter results for a particular student, term, and session
        results = Result.objects.filter(
            student_id=student_id,
            term_id=term_id,
            session_id=session_id
        )
        results_serializer = ResultSerializer(results, many=True)

        # Get the corresponding TermTotalMark if it exists
        try:
            term_total = TermTotalMark.objects.get(
                student_id=student_id,
                term_id=term_id,
                session_id=session_id
            )
            term_total_serializer = TermTotalMarkSerializer(term_total)
        except TermTotalMark.DoesNotExist:
            term_total_serializer = None

        # Combine both in one response
        return Response({
            "results": results_serializer.data,
            "term_total": term_total_serializer.data if term_total_serializer else None
        })


