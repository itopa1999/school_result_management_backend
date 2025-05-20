from rest_framework import serializers

from administrator.models import AcademicSession, ClassLevel, Result, Student, Term, TermTotalMark


class DashboardSerializer(serializers.Serializer):
    current_session = serializers.CharField()
    current_term = serializers.CharField()
    active_classes = serializers.IntegerField()    
    school_info = serializers.DictField()


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
            'c_a', 'exam', 'total_score', 'grade'
        ]


class TermTotalMarkSerializer(serializers.ModelSerializer):

    class Meta:
        model = TermTotalMark
        fields = [
            'id',
            'total_ca', 'total_exam', 'total_score',
            'grade', 'remarks'
        ]
        
        
class MainInfoSerializer(serializers.Serializer):     
    current_session_id = serializers.IntegerField()
    current_term_id = serializers.IntegerField()
    school_name = serializers.CharField()