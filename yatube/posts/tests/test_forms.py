import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='dogs',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',

        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_task_and_image_check(self):

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

        post_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        latest = Post.objects.latest("id")
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group.id, form_data['group'])
        self.assertEqual(latest.image, 'posts/small.gif')

        pages: tuple = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'UserAuthor'}),
            reverse('posts:group_list', kwargs={'slug': 'dogs'}),
        )

        for adress in pages:
            with self.subTest(adress=adress):
                response_post = self.authorized_client.get(adress)
                obj = response_post.context['page_obj'][0]
                self.assertEqual(obj.image, 'posts/small.gif')

        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': '2'}))
        obj = response.context['post']
        self.assertEqual(obj.image, 'posts/small.gif')

    def test_edit_form(self):

        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.group.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.group.id}))
        self.assertEqual(response.context['post'].text, form_data['text'])

        latest = Post.objects.latest("id")
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group.id, form_data['group'])

    def test_comments(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Коммент',
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        responseGuest = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(responseGuest, reverse(
            'users:login') + f'{"?next=/posts/1/comment/"}')
