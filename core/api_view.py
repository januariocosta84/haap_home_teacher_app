# core/api_views.py
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from core.models import ActivityResult, TeacherActivityLog, get_teacher_preschool
from core.serializers import ActivityResultSerializer

from core.serializers import LoginSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid WhatsApp number or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        if user.role == 'teacher':
            TeacherActivityLog.objects.create(
                teacher=user,
                preschool=get_teacher_preschool(user),
                activity_name='Login',
                status='success'
            )

        return Response(
            {
                "message": "Login successful",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.whatsapp_number,
                    "role": user.role,
                }
            },
            status=status.HTTP_200_OK
        )

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role == 'teacher':
            TeacherActivityLog.objects.create(
                teacher=request.user,
                preschool=get_teacher_preschool(request.user),
                activity_name='Logout',
                status='success'
            )

        request.user.auth_token.delete()
        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )



class ActivityResultCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ActivityResultSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            activity = serializer.save(
                parent=request.user  # 👈 auto-assign logged-in user
            )

            # Mirror to TeacherActivityLog so the dashboard can track teaching activity
            if request.user.role == 'teacher':
                cat1 = activity.category1 or ''
                if '-' in cat1:
                    parts = cat1.split('-', 1)
                    theme = parts[0].strip()
                    sub_theme = parts[1].strip()
                else:
                    theme = cat1.strip()
                    sub_theme = ''

                result = activity.activity_result or ''
                if result and result != 'Tentadu':
                    log_status = 'completed'
                elif result == 'Tentadu':
                    log_status = 'started'
                else:
                    log_status = 'pending'

                TeacherActivityLog.objects.create(
                    teacher=request.user,
                    preschool=get_teacher_preschool(request.user),
                    theme=theme or None,
                    sub_theme=sub_theme or None,
                    activity_name=activity.activity_name or '',
                    status=log_status,
                )

            return Response(
                {
                    "message": "Activity log created successfully",
                    "data": ActivityResultSerializer(activity).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
