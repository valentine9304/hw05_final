from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

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
            '': 200,
            '/group/dogs/': 200,
            '/profile/UserAuthor/': 200,
            '/posts/1/': 200,
            '/create/': 302,
            '/posts/1/edit/': 302,
        }

        for url, status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_login_page_exist(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_author_page_exist(self):
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_notauthor_page_exist(self):
        response = self.authorized_notauthor.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 302)

    def test_404page(self):
        response = self.guest_client.get('/page_not_exist/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/dogs/',
            'posts/profile.html': '/profile/UserAuthor/',
            'posts/post_detail.html': '/posts/1/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_template(self):
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_template(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_404_uses_correct_template(self):
        """Проверка шаблона для адреса error404."""
        response = self.guest_client.get("404")
        self.assertTrue(response.status_code == 404)
        self.assertTemplateUsed(response, 'core/404.html')
