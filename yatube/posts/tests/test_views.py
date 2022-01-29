import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testName')
        cls.user_2 = User.objects.create_user(username='justName')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{cls.group.slug}'}),
            reverse('posts:profile', kwargs={'username': f'{cls.user}'})
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostViewsTest(BaseTest):

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        template_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': f'{self.user}'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
        }
        for reverse_name, template in template_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def compair_posts(self, first_post):
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.group, self.post.group)

    def test_page_obj_context_is_showed_correctly(self):
        """Контекст 'page_obj' отображается на index, group and profile"""
        for name in self.url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                first_post = response.context['page_obj'][0]
                self.compair_posts(first_post)

    def test_group_posts_show_correct_context(self):
        """формируется список постов по group"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'})
        )
        self.assertEqual(response.context['group'].title,
                         'Тестовая группа')
        self.assertEqual(response.context['group'].slug, 'test_slug')

    def test_profile_show_correct_context(self):
        """Profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(response.context['author'], self.post.author)
        self.assertEqual(response.context['post_count'],
                         Post.objects.count())

    def test_post_detail_show_correct_context(self):
        """Пост отфильтрованный по id"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        some_post = response.context.get('post')
        self.compair_posts(some_post)

    def test_post_create_show_correct_context(self):
        """Форма создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Форма редактирования поста отфильтрованного по id"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        post_edit = response.context.get('is_edit')
        self.assertEqual(post_edit, True)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_in_right_group(self):
        """Новый пост относится только к предназначенной группе"""
        new_post = Post.objects.create(
            text='Тестовый текст 2',
            author=self.user,
            group=self.group_2
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'})
        )
        first_post = response.context['page_obj'][0]
        self.assertIsNot(first_post, new_post)

    def test_new_post_is_showed_in_right_place(self):
        """Новый пост появляется на страницах index, group_list and profile"""
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        for name in self.url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(new_post, response.context['page_obj'][0])
                self.compair_posts(new_post)

    def test_new_post_with_pictures_in_right_place(self):
        """Новый пост с img есть на страницах index, group, profile, detail"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_wth_pic = Post.objects.create(
            text='Новый текст с картинкой',
            author=self.user,
            group=self.group,
            image=uploaded,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_wth_pic.id})
        )
        self.assertEqual(response.context.get('post'), post_wth_pic)
        for name in self.url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(post_wth_pic, response.context['page_obj'][0])
                self.assertEqual(response.context['page_obj'][0].image,
                                 post_wth_pic.image.name)

    def test_cache_index_page(self):
        cache1 = self.guest_client.get(
            reverse('posts:index')
        ).content
        Post.objects.create(
            text='Новый текст для кеша',
            author=self.user,
        )
        cache2 = self.guest_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(cache1, cache2)
        cache.clear()
        self.assertNotEqual(cache2, self.guest_client.get(
            reverse('posts:index')
        ).content)


class FollowViewsTest(BaseTest):

    def test_authorized_user_can_follow(self):
        """Авторизированный пользователь может подписатьcя"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username})
        )
        follower = Follow.objects.get(user=self.user)
        self.assertEqual(self.user_2, follower.author)

    def test_follower_user_can_unfollow(self):
        """Подписчик может отписаться от автора"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username})
        )
        count_follower = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_2.username}
        ))
        again_count_follower = Follow.objects.count()
        self.assertEqual(count_follower - 1, again_count_follower)

    def test_follower_can_see_new_post(self):
        """Новый пост видят подписчики в избраном"""
        self.authorized_client_2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        ))
        new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=self.user
        )
        user_3 = User.objects.create_user(username='testuser3')
        authorized_client_3 = Client()
        authorized_client_3.force_login(user_3)
        user_2_response = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertEqual(user_2_response.context['page_obj'][0], new_post)
        user_3_response = authorized_client_3.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(user_3_response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testName')
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        objs = [
            Post(
                text='Test text',
                author=cls.user,
                group=cls.group
            )
            for i in range(13)
        ]
        cls.post = Post.objects.bulk_create(objs)

    def test_pages_have_ten_and_three_records(self):
        """На первой странице 10 записей, а на второй 3 в index и group_list"""
        urls_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'})
        ]
        for name in urls_names:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response1 = self.guest_client.get(name + '?page=2')
                self.assertEqual(len(response1.context['page_obj']), 3)
