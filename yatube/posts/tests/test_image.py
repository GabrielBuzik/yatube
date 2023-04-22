import shutil
import tempfile


from posts.forms import PostForm
from posts.models import Post, User, Group
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            author=cls.user,
            text='Тестовый пост',
            group=Group.objects.get(id=1)
        )
        cls.form = PostForm()

    def setUp(self):
        # Nonauthorized user
        self.guest_client = Client()
        # Authorized user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_with_image(self):
        """При отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных."""
        post_count = Post.objects.count()
        group = Group.objects.get(id=1)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новая запись',
            'group': group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Assert
        self.assertRedirects(response, (
            reverse('posts:profile', kwargs={'username': 'HasNoName'})
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Новая запись',
                image='posts/test.gif'
            ).exists()
        )

    def test_context_with_image(self):
        """
        При выводе поста с картинкой
        изображение передаётся в словаре context
        """
        group = Group.objects.get(id=1)
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
        Post.objects.create(
            author=self.user,
            text='Запись',
            group=group,
            image=uploaded,
        )

        reverse_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', kwargs={'slug': 'test'})),
            (reverse('posts:profile', kwargs={'username': 'HasNoName'})),
        ]

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.image, 'posts/small.gif')

        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '2'}
        ))
        self.assertEqual(response.context['post'].image, 'posts/small.gif')
