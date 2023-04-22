from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, Comment, User


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='StasBasov')
        Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user_auth,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_authorized(self):
        """Авторизированный пользователь коментирует пост"""
        сomment_count = Comment.objects.count()
        form_data = {
            'text': 'Коментарий пользователя',
        }
        response = self.authorized_client.post(
            (reverse('posts:add_comment', kwargs={'post_id': '1'})),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, (reverse('posts:post_detail', kwargs={'post_id': '1'}))
        )
        self.assertEqual(Comment.objects.count(), сomment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=1,
                text=form_data['text'],
                author=self.user
            ).exists()
        )

    def test_comment_guest(self):
        """
        Неавторизированный пользователь
        не может коментировать пост
        """
        сomment_count = Comment.objects.count()
        form_data = {
            'text': 'Коментарий анонима',
        }
        response = self.guest_client.post(
            (reverse('posts:add_comment', kwargs={'post_id': '1'})),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login') + '?next=/posts/1/comment/'
        )
        self.assertEqual(Comment.objects.count(), сomment_count)
        self.assertFalse(
            Comment.objects.filter(
                post=1,
                text=form_data['text'],
                author=self.user
            ).exists()
        )

    def test_comment_creation(self):
        """После успешной отправки комментарий появляется на странице поста."""
        Comment.objects.create(
            post=Post.objects.get(id=1),
            text='Новый коментарий',
            author=self.user,
        )
        reverse_name = reverse('posts:post_detail', kwargs={'post_id': '1'})
        response = self.authorized_client.get(reverse_name)
        first_object = response.context['comments'][0]
        post = first_object.post
        text = first_object.text
        author = first_object.author
        self.assertEqual(post.id, 1)
        self.assertEqual(text, 'Новый коментарий')
        self.assertEqual(author.username, 'StasBasov')
