from datetime import timedelta
import random
import secrets
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from administrator.models import AcademicSession, Parent, Result, SchoolProfile, Student, StudentEnrollment, Term, TermTotalMark
from administrator.parent_manager import ParentAccessCodeAuthentication
from administrator.serializers import AcademicSessionSerializer, ParentAcademicSessionSerializer, ResultSerializer, StudentEnrollmentSerializer
from authentication.serializers import ChangePasswordSerializer, ForgetPasswordSerializer
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
from drf_yasg.utils import swagger_auto_schema


def is_admin(user):
    return getattr(user, 'is_admin', False)


class ParentCreateListsView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParentListSerializer
    @swagger_auto_schema(tags=["Parent"])
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
    @swagger_auto_schema(tags=["Parent"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        if not is_admin(self.request.user):
            raise PermissionDenied("You do not have permission to perform this action.")
        
        school = SchoolProfile.objects.filter(user=self.request.user).first()
        queryset = Parent.objects.filter(school = school)
        return queryset


class ParentLoginView(APIView):
    @swagger_auto_schema(tags=["Parent"])
    def post(self, request):
        serializer = ParentLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.core.cache import cache
from django.contrib.auth.hashers import make_password


class ParentForgetPasswordView(generics.GenericAPIView):
    serializer_class = ForgetPasswordSerializer
    @swagger_auto_schema(tags=["Parent"])
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


class ParentPasswordResetVerifyView(APIView):
    @swagger_auto_schema(tags=["Parent"])
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

from rest_framework.exceptions import ParseError

class ParentChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    authentication_classes = [ParentAccessCodeAuthentication]
    @swagger_auto_schema(tags=["Parent"])
    def post(self, request, *args, **kwargs):
        print(request)
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
            try:
                parent = Parent.objects.get(email=parent.email)                
            except Parent.DoesNotExist:
                raise ParseError("Invalid parent Id.")
            
            if not parent.check_password(password):
                return Response({"error": "Old Password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            parent.set_password(password1)
            parent.save()
                
            
            return Response({'message': 'Password Changed'}, status=status.HTTP_200_OK)
    
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ParentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParentUpdateSerializer
    queryset = Parent.objects.all()
    @swagger_auto_schema(tags=["Parent"])
    def patch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")

        return self.partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=["Parent"])
    def put(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to perform this action.")

        return self.update(request, *args, **kwargs)
    
    
    
class ParentDashboardView(APIView):
    authentication_classes = [ParentAccessCodeAuthentication]
    @swagger_auto_schema(tags=["Parent"])
    def get(self, request):
        parent = request.user
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



class ParentGetSessionView(APIView):
    authentication_classes = [ParentAccessCodeAuthentication]
    @swagger_auto_schema(tags=["Parent"])
    def get(self, request):
        parent = request.user
        
        school = SchoolProfile.objects.filter(id=parent.school.id).first()
        if not school:
            return Response([])
        
        print("worked")

        sessions = AcademicSession.objects.filter(school=school)
        serializer = ParentAcademicSessionSerializer(sessions, many=True)
        return Response(serializer.data)
        
        

class ParentGetStudentsSessionView(APIView):
    authentication_classes = [ParentAccessCodeAuthentication]
    @swagger_auto_schema(tags=["Parent"])
    def get(self, request, session_id):
        parent = request.user
        
        session = AcademicSession.objects.filter(id=session_id).first()
        if not session:
            return Response({"error":"Cannot fetch school session dor students"}, status=status.HTTP_400_BAD_REQUEST)
        if not parent.school:
            return Response(
                {"error": "Parent is not associated with any school."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        parent_student_ids = parent.student.values_list('id', flat=True)
        
        students = StudentEnrollment.objects.filter(session = session, school = parent.school, student__id__in=parent_student_ids)
        serializer = StudentEnrollmentSerializer(students, many=True)
        return Response(serializer.data)
    
    
from django.db.models import Sum, Count, F
from django.db.models.functions import Coalesce

def ordinal(n):
    return f"{n}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"
class ParentShowStudentResultView(APIView):
    authentication_classes = [ParentAccessCodeAuthentication]
    @swagger_auto_schema(tags=["Parent"])
    def post(self, request, student_id, session_id, term_id):
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Invalid student"}, status=404)
        parent = request.user
        school = SchoolProfile.objects.filter(id=parent.school.id).first()
        if not school:
            return Response({"error": "School profile not found."}, status=404)
        
        admin_user = school.user.filter(is_admin=True).first()
        if not admin_user:
            return Response({"error": "No admin user found for this school."}, status=404)
        
        session = AcademicSession.objects.filter(school = school, id=session_id).first()
        if not session:
            return Response({"error": "session not available"}, status=404)
        
        if not session.show:
            return Response({"error": "session result is not available for now"}, status=404)
        
        term = Term.objects.filter(session=session, id = term_id).first()
        if not term:
            return Response({"error": "term not available"}, status=404)
        
        results = Result.objects.filter(student=student, term=term, session=session)
        if not results.exists():
            return Response({"error": "No results found for this student in the selected term and session."}, status=400)
        results_serializer = ResultSerializer(results, many=True)
        
        # Comments
        resultSummary = TermTotalMark.objects.filter(student=student, term=term, session=session).first()
        
        class_name = StudentEnrollment.objects.filter(student=student, school=school, session=session).first()    
        
        # Total score for the student
        total_score = results.aggregate(total=Coalesce(Sum('total_score'), 0))['total']
        subjects_count = results.count()
        total_possible = subjects_count * 100
        average_score = round((total_score / total_possible) * 100, 2) if total_possible else 0
        
        class_results = None
        student_ids_in_class = None
        # Class-level stats
        class_enrollment = StudentEnrollment.objects.filter(student=student, school=school, session=session).first()
        if class_enrollment:
            student_ids_in_class = StudentEnrollment.objects.filter(
                class_level=class_enrollment.class_level,
                session=session,
                school=school
            ).values_list('student', flat=True)

            # Get all results for those students in the given session and term
            class_results = Result.objects.filter(
                student_id__in=student_ids_in_class,
                session=session,
                term=term
            )
        else:
            class_results = Result.objects.none()
        
        
        # Compute each student's total
        student_scores = (
            class_results.values('student_id')
            .annotate(total=Coalesce(Sum('total_score'), 0))
            .order_by('-total')
        )
        
        
        # Calculate position
        student_position = 1
        for idx, data in enumerate(student_scores, start=1):
            if data['student_id'] == student.id:
                student_position = idx
                break
            
        # Class average
        class_total = class_results.aggregate(class_total=Coalesce(Sum('total_score'), 0))['class_total']
        total_subjects = class_results.count()
        student_total_count = student_ids_in_class.count()
        class_avg = round((class_total / (student_total_count * 100 * subjects_count)) * 100, 2) if student_total_count and subjects_count else 0

        
        
        return Response({
            "school_info": {
                "school_name": school.school_name,
                "location": school.school_address or "Not Set",
                "phone": admin_user.phone ,
                "email":  admin_user.email
            },
            "academic_sessions" : {
                "session": session.name,
                "term": term.name,
                "resumptionDate": session.next_term_date
            },
            "student" : {
                "student_name" : student.name,
                "other_info" : student.other_info,
                "class" : class_name.class_level.name or "not set"
            },
            "results" : results_serializer.data,
            "performance_summary": {
                "total_score": total_score,
                "out_of": total_possible,
                "average_score": f"{average_score}%",
                "class_average": f"{class_avg}%",
                "position": ordinal(student_position),
                "out_of_students": student_total_count
            },
            "comments":{
                "principal_comment": resultSummary.principal_comment if resultSummary and resultSummary.principal_comment else "Not Set",
                "teacher_comment": resultSummary.teacher_comment if resultSummary and resultSummary.teacher_comment else "Not Set",

            }
        })