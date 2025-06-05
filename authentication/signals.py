from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from administrator.models import AcademicSession, SchoolProfile, Term

from .models import User


@receiver(post_save, sender=User)
def Create_User_Account_Balance(sender, instance, created, **kwargs):
    if created:
        current_year = timezone.now().year
        print(current_year)
        session_name = f"{current_year - 1}/{current_year}"
        school = SchoolProfile.objects.filter(user=instance).first()
        if school:
            new_session = AcademicSession.objects.create(
                school=school,
                name=session_name,
                is_current=True
            )

            # Create terms
            term_names = ["First Term", "Second Term", "Third Term"]
            for term_name in term_names:
                Term.objects.create(
                    session=new_session,
                    name=term_name
                )