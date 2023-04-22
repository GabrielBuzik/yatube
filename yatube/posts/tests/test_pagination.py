from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='StasBasov')
        Group.objects.create(
            title='Важная группа',
            slug='important',
            description='Группа для важных постов',
        )
        Post.objects.bulk_create([Post(
            author=cls.user,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        ) for i in range(13)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_records(self):
        reverse_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', kwargs={'slug': 'important'})),
            (reverse('posts:profile', kwargs={'username': 'StasBasov'})),
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                page = response.context['page_obj']
                per_page = page.paginator.per_page
                count = page.paginator.count
                if per_page <= count:
                    self.assertEqual(len(page), per_page)
                else:
                    self.assertEqual(len(page), count)

    def test_second_page_contains_three_records(self):
        reverse_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', kwargs={'slug': 'important'})),
            (reverse('posts:profile', kwargs={'username': 'StasBasov'})),
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                if response.status_code == 200:
                    page = response.context['page_obj']
                    per_page = page.paginator.per_page
                    count = page.paginator.count - per_page
                    if per_page <= count:
                        self.assertEqual(len(page), per_page)
                    else:
                        self.assertEqual(len(page), count)
