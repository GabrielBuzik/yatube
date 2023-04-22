from posts.forms import PostForm
from posts.models import User, Post, Group
from django.test import Client, TestCase
from django.urls import reverse


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='StasBasov')
        Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        Group.objects.create(
            title='Тестовая группа 2',
            slug='test2',
            description='Тестовое описание 2',
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        )
        cls.forms = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)

        Post.objects.create(
            author=self.user_2,
            text='Тестовый пост 2',
            group=Group.objects.get(id=1)
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        group = Group.objects.get(id=1)
        form_data = {
            'text': 'Создать через форму',
            'group': group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:profile', kwargs={'username': 'StasBasov'})
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=group,
                author=self.user_2
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post_count = Post.objects.count()
        group = Group.objects.get(id=2)
        form_data = {
            'text': 'Новая запись',
            'group': group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '2'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': '2'})
        ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=group,
                author=self.user_2
            ).exists()
        )

    def test_create_post_anonymous(self):
        """
        Анонимный пользователь перенаправляется
        на регистрацию при создании поста
        """
        post_count = Post.objects.count()
        group = Group.objects.get(id=1)
        form_data = {
            'text': 'Создать через форму',
            'group': group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login') + '?next=/create/'
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=group,
            ).exists()
        )

    def test_edit_post_anonymous(self):
        post_count = Post.objects.count()
        group = Group.objects.get(id=2)
        form_data = {
            'text': 'Новая запись',
            'group': group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '2'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': '2'})
        ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=group,
            ).exists()
        )

    def test_edit_post_not_author(self):
        post_count = Post.objects.count()
        group = Group.objects.get(id=2)
        form_data = {
            'text': 'Новая запись',
            'group': group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=group,
            ).exists()
        )
