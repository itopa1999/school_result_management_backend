from django.urls import path, include
from .views import *

urlpatterns = [
    
    path('main/info/', MainInfoAPIView.as_view()),
    path('dashboard/', DashboardAPIView.as_view()),
    path('sessions/', AcademicSessionListAPIView.as_view()),
    path('add/sessions/', StartSessionView.as_view()),
    path('sessions/<int:pk>/toggle/', ToggleAcademicSessionAPIView.as_view()),
    path('terms/<int:pk>/toggle/', ToggleTermAPIView.as_view()),
    
    path('classlevels/', ClassLevelListAPIView.as_view()),
    path('classlevels/<int:class_level_id>/students/', ClassLevelStudentsAPIView.as_view()),
    path('students/<int:student_id>/', StudentDetailAPIView.as_view()),
    
    path('download/students-upload-template/', DownloadTemplateView.as_view()),
    path('download/all-students/', DownloadAllStudentsAPIView.as_view()),
    path('download/all-students/class/<int:class_id>/', DownloadAllStudentsAPIView.as_view()),
    path('preview-upload/', PreviewStudentsUploadView.as_view()),
    
    path('upload-students/', UploadStudentsView.as_view()),
    
    path('results/<int:student_id>/<int:term_id>/<int:session_id>/', ResultListCreateAPIView.as_view()),
    
    path('subjects/', SubjectsListAPIView.as_view()),
    path('subject/<int:subject_id>/', SubjectUpdateDeleteAPIView.as_view()),
    
    path('grades/', GradingListAPIView.as_view()),
    path('grade/<int:grade_id>/', GradingUpdateDeleteAPIView.as_view()),
    
    path('school-users/', SchoolUsersListView.as_view()),
    path('school/users/create/', CreateUserView.as_view()),
    path('school/users/deactivate/<int:user_id>/', DeactivateUserView.as_view()),
    
    path('subscriptions/', SubscriptionListView.as_view()),
]