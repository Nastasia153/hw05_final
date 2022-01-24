from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Это длинный тестовый текст',
        )

    def test_post_model_has_correct_object_names(self):
        """Проверка __str__ у модели post, работает корректно"""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_model_has_correct_object_name(self):
        """"Проверка __str__ у модели group, работает корректно"""
        group = PostModelTest.group
        expected_object = group.title
        self.assertEqual(expected_object, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        group = PostModelTest.group
        filds_verbose = {
            'title': 'Заголовок',
            'slug': 'Адрес для страницы группы',
            'description': 'Описание группы',
        }
        for fld, expected_value in filds_verbose.items():
            with self.subTest(field=fld):
                self.assertEqual(group._meta.get_field(fld).verbose_name,
                                 expected_value)
