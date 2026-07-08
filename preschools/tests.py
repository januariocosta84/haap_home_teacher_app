from django.test import TestCase
from django.urls import reverse

from core.models import User
from klase.models import Classroom
from preschools.models import Preschool


class ClassroomEditAccessTests(TestCase):
    def test_anonymous_user_is_redirected_to_login_for_classroom_edit(self):
        response = self.client.get(
            reverse("preschools:classroom_update", kwargs={"id": "9d07022f-cfeb-45d3-96cf-8762bfbb8f42"})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_moe_admin_can_render_classroom_edit_form(self):
        admin = User.objects.create_user(
            username="admin",
            whatsapp_number="70000001",
            password="password",
            role="moe_admin",
            first_name="MoE",
            last_name="Admin",
        )
        preschool = Preschool.objects.create(
            name="Test Preschool",
            preschool_type="government",
            created_by=admin,
        )
        classroom = Classroom.objects.create(
            preschool=preschool,
            name="Class A",
            group="A",
        )

        self.client.force_login(admin)
        response = self.client.get(
            reverse("preschools:classroom_update", kwargs={"id": classroom.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, preschool.name)
        self.assertContains(response, "Update classroom")
