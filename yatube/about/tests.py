from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about(self):
        """страница по адресу /about/author/ доступна любому пользователю"""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def tets_tech(self):
        """страница по адресу /about/tech/ доступна любому пользователю"""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
