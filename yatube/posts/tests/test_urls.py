from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import User, Post, Group
from django.urls import reverse

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='HasNoName')
        Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user_auth,
            text='Тестовый пост',
        )

    def setUp(self):
        # Nonauthorized user
        self.guest_client = Client()
        # Authorized user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        Post.objects.create(
            author=self.user,
            text='Тестовый пост 2',
        )

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны всем пользователям"""
        url_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', kwargs={'slug': 'test'})),
            (reverse('posts:profile', kwargs={'username': 'auth'})),
            (reverse('posts:post_detail', kwargs={'post_id': '1'}))
        ]
        for path in url_names:
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_accessable_authorized(self):
        """
        Страница post_edit и create доступны автору/авторизированному
        пользователю.
        """
        reverse_names = [
            (reverse('posts:post_create')),
            (reverse('posts:post_edit', kwargs={'post_id': '2'}))
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_url_that_does_not_exits(self):
        """Несуществующий путь отправляет ошибку 404"""
        response = self.guest_client.get('/somepage/')
        self.assertEqual(response.status_code, 404)

    def test_all_redirect_anonymous(self):
        """
        Страницы по адресам /create/ и я /post/edit/ перенаправит
        анонимного пользователя на нужные страницы
        """
        urls_redirects = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/posts/1/',
        }
        for url, redirect_url in urls_redirects.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_edit_authorized_not_author(self):
        """
        Страница по адресу /post/edit/ перенаправит
        пользователя, не являюшегося автором на нужную страницу.
        """
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse(
                'posts:group_list', kwargs={'slug': 'test'}
            )): 'posts/group_list.html',
            (reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            )): 'posts/post_detail.html',
            (reverse(
                'posts:post_edit', kwargs={'post_id': '2'}
            )): 'posts/create_post.html',
            (reverse(
                'posts:post_create'
            )): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
