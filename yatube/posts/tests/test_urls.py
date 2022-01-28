from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user1 = User.objects.create_user(username='Petya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст',
            group=cls.group1,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует нужный шаблон"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for urls, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(urls)
                self.assertTemplateUsed(response, template)

    def test_all_users_urls(self):
        """Страницы доступные любому пользователю."""
        pages = {
            'home': '/',
            'profile': f'/profile/{self.user}/',
            'group': f'/group/{self.group.slug}/',
            'posts': f'/posts/{self.post.id}/'
        }
        for name, address in pages.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_authorized_users_url(self):
        """Страницы доступные авторизированным пользователям"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_unexist_page_url(self):
        """Ошибка 404 отдаёт кастомный шаблон """
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_redirect_login_user_url(self):
        """Переадресация не авторизированного пользователя"""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_redirect_authorized_user_url(self):
        """Переадресация авторизированного пользователя, не автора поста"""
        response = self.authorized_client.get(f'/posts/{self.post1.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post1.id}/')
