from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import AcademicSession, Levy, StudentEnrollment, ClassLevel, StudentTermTotalFee


# add to background
@receiver(post_save, sender=AcademicSession)
def promote_students_on_new_session(sender, instance, created, **kwargs):
    if not created:
        return  # Only act on new session creation

    school = instance.school
    if not school:
        return

    # If this is the first session for the school, skip promotion
    if not AcademicSession.objects.filter(school=school).exclude(id=instance.id).exists():
        return

    previous_session = (
        AcademicSession.objects.filter(school=school)
        .exclude(id=instance.id)
        .order_by('-created_at')
        .first()
    )

    if not previous_session:
        return

    # Fetch all class levels ordered by creation (or by custom order field if you have)
    class_levels = list(ClassLevel.objects.filter(school=school).order_by("id"))
    level_map = {level.id: idx for idx, level in enumerate(class_levels)}

    previous_enrollments = StudentEnrollment.objects.filter(school=school, session=previous_session)

    @transaction.atomic
    def promote():
        for enrollment in previous_enrollments:
            current_level = enrollment.class_level
            if current_level and current_level.id in level_map:
                current_index = level_map[current_level.id]
                try:
                    next_level = class_levels[current_index + 1]
                    StudentEnrollment.objects.create(
                        student=enrollment.student,
                        class_level=next_level,
                        school=school,
                        session=instance
                    )
                except IndexError:
                    # No next level (e.g., final class), skip promotion
                    continue

    promote()


# add to background
@receiver(post_save, sender=Levy)
def create_students_levies_on_new_Levies(sender, instance, created, **kwargs):
    if not created:
        return
    
    school = instance.school
    if not school:
        return
    
    enrollments = StudentEnrollment.objects.filter(school=school)
    @transaction.atomic
    def createLevies():
        for enrollment in enrollments:
            StudentTermTotalFee.objects.create(
                student = enrollment.student,
                term = term,
                session = session, 
                levy = levy,
                
            )