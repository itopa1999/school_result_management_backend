from django.urls import path, include
from .views import *
from .results import *
from .parent import *
from .students import *
from .levy import *

urlpatterns = [
    
    # path('main/info/', MainInfoAPIView.as_view()),
    path('dashboard/', DashboardAPIView.as_view()),
    path('sessions/', AcademicSessionListAPIView.as_view()),
    path('sessions/update/<int:pk>/', SessionUpdateView.as_view()),
    path('add/sessions/', StartSessionView.as_view()),
    path('paystack-confirm-subscription/<str:reference>/', PaystackConfirmSubscriptionView.as_view(), name='paystack-confirm-subscription'),
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
    path('students/', StudentsListAPIView.as_view()),
    
    
    path('results/<int:student_id>/', ResultListAPIView.as_view()),
    
    path('subjects/', SubjectsListAPIView.as_view()),
    path('subject/<int:subject_id>/', SubjectUpdateDeleteAPIView.as_view()),
    
    path('grades/', GradingListAPIView.as_view()),
    path('grade/<int:grade_id>/', GradingUpdateDeleteAPIView.as_view()),
    
    path('school-users/', SchoolUsersListView.as_view()),
    path('school/users/create/', CreateUserView.as_view()),
    path('school/users/deactivate/<int:user_id>/', DeactivateUserView.as_view()),
    path('school-info/', SchoolDetailsView.as_view()),
    path('school-info/update/', SchoolProfileUpdateView.as_view()),
    
    path('subscriptions/', SubscriptionListView.as_view()),
    
    path('result/export/<int:student_id>/', SubjectExcelExportView.as_view()),
    path('result/preview/<int:student_id>/', UploadStudentResultPreviewView.as_view()),
    path('result/upload/', ConfirmUploadStudentResultView.as_view()),
    path('result/reset/<int:student_id>/', ResetStudentResultView.as_view()),
    path('show/result/<int:student_id>/', ShowStudentResultView.as_view()),
    path('get/comments/<int:student_id>/', GetStudentCommentView.as_view()),
    
    # parent urls
    
    path('parent/login/', ParentLoginView.as_view(), name='parent-login'),
    path('parents/', ParentCreateListsView.as_view(), name='parent-create'),
    path('parents/<int:pk>/', ParentDetailView.as_view()),
    path('parent/dashboard/', ParentDashboardView.as_view()),
    
    path("parent/forget/password/", ParentForgetPasswordView.as_view()),
    path("parent/change/password/", ParentChangePasswordView.as_view()),
    path('verify/email/<uidb64>/<token>/', ParentPasswordResetVerifyView.as_view(), name='parent-verify-email'),
    
    path("parent/get/session/lists/", ParentGetSessionView.as_view()),
    path("parent/get/students/session/lists/<int:session_id>/", ParentGetStudentsSessionView.as_view()),
    path("parent/get/students/result/<int:student_id>/<int:session_id>/<int:term_id>/", ParentShowStudentResultView.as_view()),
    
    # Levy
    
    path('levies/', LeviesListAPIView.as_view()),
    path('levies/<int:levy_id>/', LevyUpdateDeleteAPIView.as_view()),
]