from django.db import models
# Create your models here.


class SchoolProfile(models.Model):
    user = models.ManyToManyField('authentication.User')
    school_name = models.CharField(max_length=255, unique=True)
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
    school = models.ForeignKey(SchoolProfile, on_delete=models.SET_NULL, null=True, related_name='class_levels')
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]
    
    def __str__(self):
        return f"{self.school.school_name} - {self.name}"
    
    
class Student(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, related_name='students')
    name = models.CharField(max_length=100)
    other_info = models.CharField(max_length=100,blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Calculate CA and total score
        self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]
        
    def __str__(self):
        return self.name
    
    
class AcademicSession(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.SET_NULL, null=True, related_name="sessions")
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
    session = models.ForeignKey(AcademicSession, on_delete=models.SET_NULL, null=True, related_name="terms")
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
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, related_name='student_result')
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, related_name='result_term')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=20)
    first_test = models.PositiveIntegerField(blank=True, null=True)
    second_test = models.PositiveIntegerField(blank=True, null=True)
    third_test = models.PositiveIntegerField(blank=True, null=True)
    c_a = models.PositiveIntegerField(blank=True, null=True)
    exam = models.PositiveIntegerField(blank=True, null=True)
    total_score = models.PositiveIntegerField(blank=True, null=True)
    grade = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate CA and total score
        self.c_a = (self.first_test or 0) + (self.second_test or 0) + (self.third_test or 0)
        self.total_score = self.c_a + (self.exam or 0)

        # Fetch grade from GradingSystem based on this student's school
        school = self.session.school  # assumes session has FK to SchoolProfile
        grading = GradingSystem.objects.filter(
            school=school,
            min_score__lte=self.total_score,
            max_score__gte=self.total_score
        ).first()

        self.grade = grading.grade if grading else 'N/A'

        # Save the result first
        super().save(*args, **kwargs)

        # Aggregate all results for this student in this term and session
        agg = Result.objects.filter(
            student=self.student,
            term=self.term,
            session=self.session
        ).aggregate(
            total_ca=Sum('c_a'),
            total_exam=Sum('exam'),
            total_score=Sum('total_score')
        )

        total_score = agg['total_score'] or 0

        # Get overall grade for the term
        term_grading = GradingSystem.objects.filter(
            school=school,
            min_score__lte=total_score,
            max_score__gte=total_score
        ).first()

        term_grade = term_grading.grade if term_grading else 'N/A'
        remarks = term_grading.remark if term_grading else ''

        # Update or create the TermTotalMark record
        TermTotalMark.objects.update_or_create(
            student=self.student,
            term=self.term,
            session=self.session,
            defaults={
                'total_ca': agg['total_ca'] or 0,
                'total_exam': agg['total_exam'] or 0,
                'total_score': total_score,
                'grade': term_grade,
                'remarks': remarks,
            }
        )
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-subjects', '-session']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.term.name} ({self.term.session.name})"
    
    
class TermTotalMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, related_name='term_totals')
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, related_name='term_totals')
    session = models.ForeignKey(AcademicSession, on_delete=models.SET_NULL, null=True, related_name='term_totals')
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
    
    
    

# settings

class Subject(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.SET_NULL, null=True, related_name='class_subjects')
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def save(self, *args, **kwargs):
        # Calculate CA and total score
        self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-name']),
        ]
    
    def __str__(self):
        return f"{self.school.school_name} - {self.name}"
    
    
    
class GradingSystem(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.SET_NULL, null=True, related_name='school_grading_system')
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    grade = models.CharField(max_length=2)
    remark = models.CharField(max_length=255)

    class Meta:
        ordering = ['-min_score']  # ensures highest ranges come first

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score})"
    

from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
    
class Subscription(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    school = models.ForeignKey(SchoolProfile, on_delete=models.SET_NULL, null=True, related_name="sub_sessions")
    session = models.CharField(max_length=50)
    paid_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        today = timezone.now().date()

        # Set default expiry if not already set
        if not self.expires_on:
            self.expires_on = today + timedelta(weeks=14)  # 3 months + 1 week

        # Update status based on expiry
        if self.expires_on < today:
            self.status = 'expired'
        elif self.status != 'expired':
            # Retain original status if still valid
            self.status = 'active' if self.paid_on else 'free'

        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-id']),
        ]

    def __str__(self):
        return f"{self.session} - {self.status.capitalize()}"