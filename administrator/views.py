import secrets
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
import requests as req
from django.utils import timezone
# Create your views here.


from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from administrator.serializers import AcademicSessionSerializer, ClassLevelSerializer, CreateUserSerializer, DashboardSerializer, GradeSystemSerializer, MainInfoSerializer, ResultSerializer, SchoolProfileSerializer, StudentEnrollmentSerializer, StudentSerializer, StudentUploadPreviewSerializer, SubjectsSerializer, SubscriptionSerializer, TermTotalMarkSerializer, UserSerializer
from authentication.models import User
from .models import AcademicSession, ClassLevel, GradingSystem, Result, Student, StudentEnrollment, Subject, Subscription, Term, SchoolProfile, TermTotalMark
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


# class MainInfoAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Get the school for the current user
#         user = request.user
#         school = SchoolProfile.objects.filter(user=user).first()
        
#         if not school:
#             return Response({"detail": "No school profile associated with user."}, status=404)

#         current_session = AcademicSession.objects.filter(school=school, is_current=True).first()
#         current_term = Term.objects.filter(session=current_session, is_current=True).first()
        
#         # Example fallback values
#         session_id = current_session.id if current_session else 0
#         term_id = current_term.id if current_term else 0

#         data = {
#             "current_session_id": session_id,
#             "current_term_id": term_id,
#             "school_name": school.school_name,
#         }

#         serializer = MainInfoSerializer(data)
#         return Response(serializer.data)
    
    
def is_admin(user):
    return getattr(user, 'is_admin', False)

def is_manager(user):
    return getattr(user, 'is_manager', False)


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        # Get the school for the current user
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        
        if not school:
            return Response({"detail": "No school profile associated with user."}, status=404)

        current_session = AcademicSession.objects.filter(school=school, is_current=True).first()
        current_term = Term.objects.filter(session=current_session, is_current=True).first()
        active_classes = ClassLevel.objects.filter(school=school).count()
        students = Student.objects.filter(school = school).count()
        subjects = Subject.objects.filter(school__user = user).count()
        # Example fallback values
        session_name = current_session.name if current_session else "Not Set"
        term_name = current_term.name if current_term else "Not Set"
        
        current_sub = Subscription.objects.filter(school=school).first()
        
        serializer_current_sub = SubscriptionSerializer(current_sub).data if current_sub else None
        print(serializer_current_sub)
        data = {
            "current_session": session_name,
            "current_term": term_name,
            "active_classes": active_classes,
            "total_subjects":subjects,
            "school_info": {
                "school_name": school.school_name,
                "location": school.school_address or "Not Set",
                "total_students": students 
            },
            "subscription_info": serializer_current_sub

        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)
    
    

class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        session_name = request.data.get("session_name")
        is_current_session = request.data.get("is_current", False)
        if isinstance(is_current_session, str):
            is_current_session = is_current_session.lower() == 'true'
        user = request.user
        if not session_name:
            return Response({"error": "session_name and school_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            school = SchoolProfile.objects.filter(user=user).first()
        except SchoolProfile.DoesNotExist:
            return Response({"error": "School not found."}, status=status.HTTP_404_NOT_FOUND)

        if AcademicSession.objects.filter(school=school, name=session_name).exists():
            return Response({"error": f"Session '{session_name}' already exists for this school."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not AcademicSession.objects.filter(school=school).exists():
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
                
                Subscription.objects.create(
                    school = school,
                    session = f"{new_session.name} session"
                )

            return Response({"message": f"Session '{session_name}' created with 3 terms."},
                            status=status.HTTP_201_CREATED)
        
        else:
            ref = secrets.token_urlsafe(15)
            amount = int(float(settings.SUBSCRIPTION_PRICE)) * 100
            
            redirect_url = request.build_absolute_uri(
                reverse('paystack-confirm-subscription', kwargs={"reference": ref})
            )
            
            paystack_data = {
                "email": user.email,
                "amount": amount,
                "reference": ref,
                "metadata": {
                    "school_id" : school.id,
                    "session_name": f"{session_name} session",
                    "is_current_session" : is_current_session,
                },
                "callback_url": redirect_url,
            }
            
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }

            paystack_url = "https://api.paystack.co/transaction/initialize"
            response = req.post(paystack_url, headers=headers, json=paystack_data)

            if response.status_code == 200:
                link = response.json()["data"]["authorization_url"]
                return Response({"checkout_url": link}, status=status.HTTP_200_OK)

            return Response({"error": "Could not initialize payment."}, status=response.status_code)
            



class PaystackConfirmSubscriptionView(APIView):
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, reference, *args, **kwargs):
        if not reference:
            return Response({"error": "Reference is required"}, status=400)

        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        response = req.get(url, headers=headers)
        data = response.json()

        if data['status'] and data['data']['status'] == 'success':
            metadata = data['data']['metadata']
            
            print(metadata)
            school_id = metadata.get("school_id")
            session_name = metadata.get("session_name")
            is_current_session = metadata.get("is_current_session", False)
            if isinstance(is_current_session, str):
                is_current_session = is_current_session.lower() == 'true'
            school = SchoolProfile.objects.get(id=school_id)
            
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
                Subscription.objects.create(
                    school = school,
                    session = session_name,
                    paid_on = timezone.now()
                )
        

            return Response({"message": "Subscription was successful."}, status=200)
        return Response({"error": "Subscription was unsuccessful."}, status=400)
    


class AcademicSessionListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        user = request.user
        if not is_admin(user):
            raise PermissionDenied("You do not have permission to perform this action.")
        
        school = SchoolProfile.objects.filter(user=user).first()
        if not school:
            return Response([])

        sessions = AcademicSession.objects.filter(school=school)
        serializer = AcademicSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    
class ToggleAcademicSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request, pk):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
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
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request, pk):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
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
    
    

class SessionUpdateView(generics.GenericAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])        
    def put(self, request, pk):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            session = self.get_queryset().get(pk=pk)
        except AcademicSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Session updated successfully."}, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class ClassLevelListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        class_levels = ClassLevel.objects.filter(school=school)
        serializer = ClassLevelSerializer(class_levels, many=True)
        return Response(serializer.data)

class ClassLevelStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, class_level_id):
        class_level = get_object_or_404(ClassLevel, id=class_level_id)
        school = SchoolProfile.objects.filter(user=request.user).first()
        session = AcademicSession.objects.filter(school = school, is_current=True).first()
        students = StudentEnrollment.objects.filter(class_level=class_level, session = session, school = school)
        serializer = StudentEnrollmentSerializer(students, many=True)
        return Response(serializer.data)

class StudentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Admins"])
    def put(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = StudentSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Admins"])
    def delete(self, request, student_id):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class SubjectsListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        subjects = Subject.objects.filter(school=school)
        serializer = SubjectsSerializer(subjects, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        name = request.data.get("name", "").strip()

        # Check for duplicate name in the same school
        if Subject.objects.filter(school=school, name__iexact=name).exists():
            return Response(
                {"error": "Subject with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new subject
        subject = Subject.objects.create(school=school, name=name)
        serializer = SubjectsSerializer(subject)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class SubjectUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def put(self, request, subject_id):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        subject = get_object_or_404(Subject, id=subject_id)
        serializer = StudentSerializer(subject, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Admins"])
    def delete(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    
    
class GradingListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        grade = GradingSystem.objects.filter(school=school)
        serializer = GradeSystemSerializer(grade, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()

        # Extract fields from request.data
        min_score = request.data.get('min_score')
        max_score = request.data.get('max_score')
        grade = request.data.get('grade')
        remark = request.data.get('remark')

        data = {
            'min_score': min_score,
            'max_score': max_score,
            'grade': grade,
            'remark': remark,
        }

        serializer = GradeSystemSerializer(data=data)
        if serializer.is_valid():
            serializer.save(school=school)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class GradingUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def put(self, request, grade_id):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        grade = get_object_or_404(GradingSystem, id=grade_id)
        serializer = GradeSystemSerializer(grade, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Admins"])
    def delete(self, request, grade_id):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        grade = get_object_or_404(GradingSystem, id=grade_id)
        grade.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

import csv
class DownloadAllStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, *args, **kwargs):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        if not school:
            return HttpResponse("School not found for the user.", status=400)

        class_levels = ClassLevel.objects.filter(school=school).prefetch_related('students')

        if not class_levels.exists():
            return HttpResponse("No class levels found.", status=400)

        # Use Django HttpResponse to generate CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_students.csv"'

        writer = csv.writer(response)
        writer.writerow(['Name', 'Other Info', 'Class'])

        for class_level in class_levels:
            for student in class_level.students.all():
                writer.writerow([
                    student.student.name,
                    student.student.other_info or '',
                    class_level.name
                ])

        return response

    
    
class SchoolProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        serializer = SchoolProfileSerializer(school)
        return Response(serializer.data)
    
    @swagger_auto_schema(tags=["Admins"])
    def put(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        serializer = SchoolProfileSerializer(school, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    

class SchoolUsersListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        user = request.user

        # Get the school profile where this user is one of the admins
        school = SchoolProfile.objects.filter(user=user).first()
        if not school:
            return Response({'error': 'School not found for this user.'}, status=404)

        # Get all users related to the school excluding the current user
        users = school.user.exclude(id=user.id)

        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)
    
    
    
    
class CreateUserView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        email = serializer.validated_data['email']
        user = User.objects.create_user(
            email=email,
            password='pass1234',
            is_active=True,
            is_manager = True,
            phone = self.request.user.phone
        )
        
        school = SchoolProfile.objects.filter(user=self.request.user).first()
        school.user.add(user)
    
        
        
class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def post(self, request, user_id, *args, **kwargs):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            return Response({"message": True, "is_active": user.is_active}, status=201)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        
        
        
class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = self.request.user
        school = SchoolProfile.objects.filter(user=user).first()
        return Subscription.objects.filter(school=school).order_by('-expires_on')
    

from rest_framework.pagination import PageNumberPagination
class StudentPagination(PageNumberPagination):
    page_size = 40
    max_page_size = 40 
    
    
class StudentsListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        
        session = AcademicSession.objects.filter(school = school, is_current=True).first()
        students = StudentEnrollment.objects.filter(session = session, school = school)        
        paginator = StudentPagination()
        paginated_students = paginator.paginate_queryset(students, request)
        serializer = StudentEnrollmentSerializer(paginated_students, many=True)

        return paginator.get_paginated_response(serializer.data)
    
    
    
class SchoolDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request):
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        print("school:", school)
        serializer = SchoolProfileSerializer(school)
        print("serialized data:", serializer.data)
        return Response({"school": serializer.data}, status=200)
    
    
    
class SchoolProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def put(self, request):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        user = request.user
        school = SchoolProfile.objects.filter(user=user).first()
        if not school:
            return Response({"error": "School profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SchoolProfileSerializer(school, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    

class GetStudentCommentView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["Admins"])
    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Invalid student"}, status=404)
        
        school = SchoolProfile.objects.filter(user=request.user).first()
        if not school:
            return Response({"error": "School profile not found."}, status=404)
                
        session = AcademicSession.objects.filter(school = school, is_current=True).first()
        if not session:
            return Response({"error": "session not set"}, status=404)
        
        term = Term.objects.filter(session=session, is_current=True).first()
        if not term:
            return Response({"error": "term not set"}, status=404)
        
        resultSummary = TermTotalMark.objects.filter(student=student, term=term, session=session).first()
        
        return Response({
            "principal_comment": resultSummary.principal_comment if resultSummary and resultSummary.principal_comment else "Not Set",
            "teacher_comment": resultSummary.teacher_comment if resultSummary and resultSummary.teacher_comment else "Not Set",

        }, status=200)