from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserAuthor')
        cls.notauthor = User.objects.create_user(username='UserNotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='dogs',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_notauthor = Client()
        self.authorized_notauthor.force_login(self.notauthor)

    def test_guest_pages_exists(self):
        urls = {
            '': HTTPStatus.OK,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:profile', kwargs={'username': self.user}): HTTPStatus.OK,
            reverse('posts:post_detail', kwargs={'post_id': self.group.pk}): HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            reverse('posts:post_edit', kwargs={'post_id': self.group.pk}): HTTPStatus.FOUND,
        }

        for url, status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_login_page_exist(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_page_exist(self):
        response = self.authorized_client.get(reverse('posts:post_edit', kwargs={'post_id': self.group.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_notauthor_page_exist(self):
        response = self.authorized_notauthor.get(reverse('posts:post_edit', kwargs={'post_id': self.group.pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404page(self):
        response = self.guest_client.get('/page_not_exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile', kwargs={'username': self.user}),
            'posts/post_detail.html':  reverse('posts:post_detail', kwargs={'post_id': self.group.pk}),
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_template(self):
        response = self.authorized_client.get(reverse('posts:post_edit', kwargs={'post_id': self.group.pk}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_template(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_404_uses_correct_template(self):
        """Проверка шаблона для адреса error404."""
        response = self.guest_client.get("404")
        self.assertTrue(response.status_code == HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
