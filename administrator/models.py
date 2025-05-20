from django.db import models
# Create your models here.


class SchoolProfile(models.Model):
    user = models.ManyToManyField('authentication.User')
    school_name = models.CharField(max_length=255)
    school_address = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    is_secondary = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-school_name']),
        ]
    
    def save(self, *args, **kwargs):
        self.school_name = self.school_name.capitalize()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.school_name

class ClassLevel(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='class_levels')
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]
    
    def __str__(self):
        return f"{self.school.school_name} - {self.name}"
    
    
class Student(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=100)
    other_info = models.CharField(max_length=100,blank=True, null=True)
        
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]
        
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
            self.name = self.name[0].upper() + self.name[1:]
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
    
class AcademicSession(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name="sessions")
    name = models.CharField(max_length=20)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]

    
    def __str__(self):
        return self.name

class Term(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=20)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]

    def __str__(self):
        return f"{self.name} - {self.session.name}"
    
from django.db.models import Sum
    
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_result')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='result_term')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    subjects =  models.CharField(max_length=20)
    first_test = models.PositiveIntegerField(blank=True, null=True)
    second_test = models.PositiveIntegerField(blank=True, null=True)
    third_test = models.PositiveIntegerField(blank=True, null=True)
    c_a = models.PositiveIntegerField(blank=True, null=True)
    exam = models.PositiveIntegerField(blank=True, null=True)
    total_score = models.PositiveIntegerField(blank=True, null=True)
    grade =  models.CharField(max_length=20,blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Calculate total_score
        self.c_a = self.first_test + self.second_test + self.third_test 
        exam = self.exam or 0
        self.total_score = self.c_a + exam
        
        # Determine grade based on total_score (using Nigerian grading system example)
        if self.total_score >= 70:
            self.grade = 'A'
        elif self.total_score >= 60:
            self.grade = 'B'
        elif self.total_score >= 50:
            self.grade = 'C'
        elif self.total_score >= 45:
            self.grade = 'D'
        elif self.total_score >= 40:
            self.grade = 'E'
        else:
            self.grade = 'F'
        
        super().save(*args, **kwargs)
        
        
        # Aggregate total CA, exam, total_score for this student and term
        agg = Result.objects.filter(student=self.student, term=self.term, session = self.session).aggregate(
            total_ca=Sum('c_a'),
            total_exam=Sum('exam'),
            total_score=Sum('total_score')
        )
        
        # Calculate overall term grade based on total_score
        total_score = agg['total_score'] or 0
        
        if total_score >= 70:
            term_grade = 'A'
        elif total_score >= 60:
            term_grade = 'B'
        elif total_score >= 50:
            term_grade = 'C'
        elif total_score >= 45:
            term_grade = 'D'
        elif total_score >= 40:
            term_grade = 'E'
        else:
            term_grade = 'F'
        
        # Update or create TermTotalMark entry
        TermTotalMark.objects.update_or_create(
            student=self.student,
            term=self.term,
            session = self.session,
            defaults={
                'total_ca': agg['total_ca'] or 0,
                'total_exam': agg['total_exam'] or 0,
                'total_score': total_score,
                'grade': term_grade,
                'remarks': self.get_remarks(term_grade),
            }
        )

    def get_remarks(self, grade):
        remarks_map = {
            'A': 'Excellent performance',
            'B': 'Very good',
            'C': 'Good',
            'D': 'Fair',
            'E': 'Pass',
            'F': 'Fail',
        }
        return remarks_map.get(grade, '')
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-subjects', '-session']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.term.name} ({self.term.session.name})"
    
    
class TermTotalMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='term_totals')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='term_totals')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='term_totals')
    total_ca = models.PositiveIntegerField(default=0)     # Continuous Assessment total
    total_exam = models.PositiveIntegerField(default=0)   # Exam total
    total_score = models.PositiveIntegerField(default=0)  # Overall total score for the term
    
    grade = models.CharField(max_length=5, blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'term', 'session')
        ordering = ['term']

    def __str__(self):
        return f"{self.student.name} - {self.session.name} - {self.term.name}"