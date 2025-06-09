from rest_framework import serializers

from administrator.models import AcademicSession, ClassLevel, GradingSystem, Result, SchoolProfile, Student, StudentEnrollment, Subject, Subscription, Term, TermTotalMark
from authentication.models import User



class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'session', 'status', 'paid_on', 'expires_on']

class DashboardSerializer(serializers.Serializer):
    current_session = serializers.CharField()
    current_term = serializers.CharField()
    active_classes = serializers.IntegerField()  
    total_subjects = serializers.IntegerField()    
    school_info = serializers.DictField()
    subscription_info = SubscriptionSerializer(allow_null=True)


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['id', 'name', 'is_current']
    
class AcademicSessionSerializer(serializers.ModelSerializer):
    terms = TermSerializer(many=True, read_only=True)
    class Meta:
        model = AcademicSession
        fields = ['id', 'name', 'is_current','terms']
        
class ClassLevelSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = ClassLevel
        fields = ['id', 'name', 'school_name']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'other_info']
        

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    class_level = serializers.CharField(source='class_level.name', read_only=True)
    student = StudentSerializer()
    class Meta:
        model = StudentEnrollment
        fields = ['id', 'student','class_level']



class ResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    session_name = serializers.CharField(source='session.name', read_only=True)

    class Meta:
        model = Result
        fields = [
            'id','student_name',
            'term_name',
            'session_name',
            'subjects', 'first_test', 'second_test', 'third_test',
            'c_a', 'exam', 'total_score', 'grade', 'remark'
        ]


class TermTotalMarkSerializer(serializers.ModelSerializer):

    class Meta:
        model = TermTotalMark
        fields = [
            'id',
            'total_ca', 'total_exam', 'total_score',
            'grade', 'remarks'
        ]
        

class SubjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']
        
        
class GradeSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingSystem
        fields = ['id', 'min_score','max_score','grade','remark']
                  
                  
class MainInfoSerializer(serializers.Serializer):     
    current_session_id = serializers.IntegerField()
    current_term_id = serializers.IntegerField()
    school_name = serializers.CharField()
    
    
class SchoolProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolProfile
        fields = ['id', 'school_name','school_address']
        
        
class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','email', 'is_active', 'profile_picture']
        
    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return request.build_absolute_uri(obj.profile_picture.url)
        return None
    
    
class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']
        
        
