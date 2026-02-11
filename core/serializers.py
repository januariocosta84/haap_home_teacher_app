# core/serializers.py
from rest_framework import serializers

from core.models import ActivityResult

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()   # WhatsApp number
    password = serializers.CharField(write_only=True)


class ActivityResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityResult
        fields = [
            "id",
            "student",
            "category1",
            "category2",
            "category3",
            "activity_name",
            "activity_result",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_student(self, student):
        """
        Optional but recommended:
        Ensure the student belongs to the logged-in parent
        """
        request = self.context.get("request")
        if student.parent != request.user:
            raise serializers.ValidationError(
                "You are not allowed to log activity for this student."
            )
        return student
