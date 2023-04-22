from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Group, Post, Follow

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        Post.objects.create(
            author=self.user,
            text='Тестовый пост 2',
            group=Group.objects.get(id=1)
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={'slug': 'test'})):
            'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': 'auth'})):
            'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': '1'})):
            'posts/post_detail.html',
            (reverse('posts:post_create')):
            'posts/create_post.html',
            (reverse('posts:post_edit', kwargs={'post_id': '2'})):
            'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_count_is_2(self):
        """Контекст главной страницы содержит 2 поста"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'].object_list.__len__(), 2)

    def test_group_list_count_is_2(self):
        """Контекст главной страницы содержит 2 поста"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test'})
        )
        self.assertEqual(response.context['page_obj'].object_list.__len__(), 2)

    def test_profile_count_is_1(self):
        """Контекст пользователя содержит 1 пост"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'StasBasov'})
        )
        self.assertEqual(response.context['page_obj'].object_list.__len__(), 1)

    def test_show_correct_context(self):
        """Шаблоны index,group_list,profile
        сформирован с правильным контекстом."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test'}),
            reverse('posts:profile', kwargs={'username': 'StasBasov'})

        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                text_0 = first_object.text
                author_name_0 = first_object.author.username
                group_name_0 = first_object.group.title
                self.assertEqual(text_0, 'Тестовый пост 2')
                self.assertEqual(author_name_0, 'StasBasov')
                self.assertEqual(group_name_0, 'Тестовая группа')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        ))
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(response.context.get('post').author.username, 'auth')
        self.assertEqual(
            response.context.get('post').group.title, 'Тестовая группа'
        )

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '2'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_creation(self):
        """Пост отображается при создании."""
        Post.objects.create(
            author=self.user,
            text='Новый пост',
            group=Group.objects.get(id=1)
        )
        reverse_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', kwargs={'slug': 'test'})),
            (reverse('posts:profile', kwargs={'username': 'StasBasov'})),
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                text_0 = first_object.text
                author_name_0 = first_object.author.username
                group_name_0 = first_object.group.title
                self.assertEqual(text_0, 'Новый пост')
                self.assertEqual(author_name_0, 'StasBasov')
                self.assertEqual(group_name_0, 'Тестовая группа')

    def test_cache_index(self):
        """
        Список постов на главной странице сайта хранится в кэше и обновляется.
        """
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        )

        first_response_content = self.guest_client.get(
            reverse('posts:index')
        ).content
        post.delete()

        second_response_content = self.guest_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(first_response_content, second_response_content)
        cache.clear()
        third_response_content = self.guest_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(third_response_content, second_response_content)

    def test_follow(self):
        """Тестирование подписки на автора."""
        count_follow = Follow.objects.count()
        author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Тестирование отписки от автора."""
        count_follow = Follow.objects.count()
        author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        response_follow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_follow = response_follow.context
        post = context_follow['page_obj'][0]
        text = post.text
        author = post.author
        group = post.group
        self.assertEqual(text, 'Тестовый пост 2')
        self.assertEqual(author.username, 'StasBasov')
        self.assertEqual(group.title, 'Тестовая группа')

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        response_unfollow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)
