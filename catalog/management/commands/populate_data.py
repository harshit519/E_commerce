from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate the database with sample categories and products'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Latest electronic gadgets and devices'},
            {'name': 'Clothing', 'description': 'Fashionable clothing for all ages'},
            {'name': 'Books', 'description': 'Educational and entertainment books'},
            {'name': 'Home & Garden', 'description': 'Everything for your home and garden'},
            {'name': 'Sports', 'description': 'Sports equipment and accessories'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create products
        products_data = [
            {
                'name': 'Smartphone X1',
                'category': 'Electronics',
                'price': Decimal('599.99'),
                'description': 'Latest smartphone with advanced features, high-resolution camera, and long battery life.',
                'stock': 50
            },
            {
                'name': 'Wireless Headphones',
                'category': 'Electronics',
                'price': Decimal('89.99'),
                'description': 'Premium wireless headphones with noise cancellation and 30-hour battery life.',
                'stock': 100
            },
            {
                'name': 'Casual T-Shirt',
                'category': 'Clothing',
                'price': Decimal('24.99'),
                'description': 'Comfortable cotton t-shirt available in multiple colors and sizes.',
                'stock': 200
            },
            {
                'name': 'Denim Jeans',
                'category': 'Clothing',
                'price': Decimal('59.99'),
                'description': 'Classic denim jeans with perfect fit and durability.',
                'stock': 150
            },
            {
                'name': 'Python Programming Book',
                'category': 'Books',
                'price': Decimal('39.99'),
                'description': 'Comprehensive guide to Python programming for beginners and advanced users.',
                'stock': 75
            },
            {
                'name': 'Fiction Novel Collection',
                'category': 'Books',
                'price': Decimal('29.99'),
                'description': 'Bestselling fiction novels from top authors around the world.',
                'stock': 120
            },
            {
                'name': 'Garden Tool Set',
                'category': 'Home & Garden',
                'price': Decimal('79.99'),
                'description': 'Complete set of essential garden tools for professional and home use.',
                'stock': 60
            },
            {
                'name': 'Indoor Plant Pot',
                'category': 'Home & Garden',
                'price': Decimal('19.99'),
                'description': 'Beautiful ceramic plant pots for indoor plants and decoration.',
                'stock': 200
            },
            {
                'name': 'Basketball',
                'category': 'Sports',
                'price': Decimal('34.99'),
                'description': 'Official size basketball perfect for indoor and outdoor play.',
                'stock': 80
            },
            {
                'name': 'Yoga Mat',
                'category': 'Sports',
                'price': Decimal('44.99'),
                'description': 'Premium yoga mat with excellent grip and cushioning for comfortable practice.',
                'stock': 100
            },
        ]
        
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'category': categories[prod_data['category']],
                    'price': prod_data['price'],
                    'description': prod_data['description'],
                    'stock': prod_data['stock'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create a superuser if none exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@shophub.com', 'admin123')
            self.stdout.write('Created superuser: admin (password: admin123)')
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('You can now login with:')
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')
