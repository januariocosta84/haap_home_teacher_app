# core/api_views.py
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from core.models import ActivityResult
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
