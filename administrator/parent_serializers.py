from rest_framework import serializers
from .models import Parent, SchoolProfile, Student
from rest_framework.exceptions import ParseError


class ParentCreateSerializer(serializers.ModelSerializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    class Meta:
        model = Parent
        fields = ['name', 'email', 'student_ids']
        
        
    def validate_student_ids(self, student_ids):
        # Check if any of the students are already linked to a parent
        claimed_students = Parent.objects.filter(student__in=student_ids).values_list('student__id', flat=True)

        if claimed_students:
            claimed_names = Student.objects.filter(id__in=claimed_students).values_list('name', flat=True)
            names_str = ', '.join(claimed_names)
            raise ParseError(f"The following student(s) are already assigned to a parent: {names_str}")

        return student_ids

    def create(self, validated_data):
        student_ids = validated_data.pop('student_ids')
        password = "pass1234"

        parent = Parent(**validated_data)
        parent.set_password(password)
        parent.save()
        parent.student.set(student_ids)
        return parent

class ParentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            parent = Parent.objects.get(email=email)
            school = SchoolProfile.objects.filter(school_name=parent.school.school_name).first()
            
        except Parent.DoesNotExist:
            raise ParseError("Invalid email or password.")

        if not parent.check_password(password):
            raise ParseError("Invalid email or password.")

        # Generate a new access code on login
        parent.regenerate_access_code()

        return {
            "parent_name": parent.name,
            "access_code": parent.access_code,
            "school_name":school.school_name,
            "school_location" : school.school_address
        }
        
        

class StudentNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'other_info']

class ParentListSerializer(serializers.ModelSerializer):
    students = StudentNestedSerializer(many=True, source='student')

    class Meta:
        model = Parent
        fields = ['id', 'name', 'email', 'is_active', 'students']
        
        

class ParentUpdateSerializer(serializers.ModelSerializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Parent
        fields = ['name', 'email', 'student_ids', 'is_active']

    def validate_student_ids(self, value):
        # Check if any of the students are already claimed by another parent
        for student_id in value:
            if Parent.objects.filter(student__id=student_id).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(f"Student {student_id} is already claimed.")
        return value

    def update(self, instance, validated_data):
        student_ids = validated_data.pop('student_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if student_ids is not None:
            instance.student.set(student_ids)
        return instance
