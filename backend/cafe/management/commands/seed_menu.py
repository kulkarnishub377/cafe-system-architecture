"""
Management command: seed_menu
Seeds the database with the initial # SK cafe menu items and default settings.

Usage:
    python manage.py seed_menu          # create only (skip if exists)
    python manage.py seed_menu --reset  # wipe and recreate
"""

from django.core.management.base import BaseCommand

from cafe.models import CafeSettings, MenuItem

MENU_ITEMS = [
    # Coffee
    {"name": "Caramel Macchiato", "price": 220, "category": "coffee",
     "image": "https://images.unsplash.com/photo-1485808191679-5f86510681a2?w=400",
     "emoji": "☕", "is_veg": True, "trending": True,
     "description": "Espresso with vanilla & caramel drizzle", "calories": 180},
    {"name": "Iced Latte", "price": 180, "category": "coffee",
     "image": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400",
     "emoji": "🧊", "is_veg": True, "trending": True,
     "description": "Chilled espresso with creamy milk", "calories": 120},
    {"name": "Espresso Shot", "price": 120, "category": "coffee",
     "image": "https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400",
     "emoji": "⚡", "is_veg": True, "trending": False,
     "description": "Pure concentrated coffee", "calories": 5},
    {"name": "Mocha Frappe", "price": 250, "category": "coffee",
     "image": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400",
     "emoji": "🍫", "is_veg": True, "trending": False,
     "description": "Blended chocolate coffee delight", "calories": 290},
    {"name": "Cappuccino", "price": 180, "category": "coffee",
     "image": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400",
     "emoji": "☕", "is_veg": True, "trending": False,
     "description": "Classic Italian coffee with foam", "calories": 140},
    # Burgers
    {"name": "Classic Smash Burger", "price": 320, "category": "burgers",
     "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
     "emoji": "🍔", "is_veg": False, "trending": True,
     "description": "Juicy double patty with special sauce", "calories": 650},
    {"name": "Cheese Overload", "price": 380, "category": "burgers",
     "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400",
     "emoji": "🧀", "is_veg": False, "trending": False,
     "description": "Triple cheese melted burger", "calories": 720},
    {"name": "Veggie Supreme", "price": 280, "category": "burgers",
     "image": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=400",
     "emoji": "🥗", "is_veg": True, "trending": False,
     "description": "Fresh garden veggie patty", "calories": 380},
    {"name": "Chicken Zinger", "price": 340, "category": "burgers",
     "image": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400",
     "emoji": "🍗", "is_veg": False, "trending": True,
     "description": "Crispy spicy chicken burger", "calories": 580},
    # Pizza
    {"name": "Margherita", "price": 350, "category": "pizza",
     "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400",
     "emoji": "🍕", "is_veg": True, "trending": True,
     "description": "Classic tomato basil cheese", "calories": 450},
    {"name": "Pepperoni Feast", "price": 450, "category": "pizza",
     "image": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400",
     "emoji": "🔥", "is_veg": False, "trending": False,
     "description": "Loaded with pepperoni slices", "calories": 620},
    {"name": "BBQ Chicken", "price": 480, "category": "pizza",
     "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",
     "emoji": "🍗", "is_veg": False, "trending": False,
     "description": "Smoky BBQ chicken pizza", "calories": 580},
    {"name": "Veggie Delight", "price": 380, "category": "pizza",
     "image": "https://images.unsplash.com/photo-1511689660979-10d2b1aada49?w=400",
     "emoji": "🥬", "is_veg": True, "trending": False,
     "description": "Garden fresh vegetables", "calories": 420},
    # Desserts
    {"name": "Molten Brownie", "price": 180, "category": "desserts",
     "image": "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400",
     "emoji": "🍫", "is_veg": True, "trending": False,
     "description": "Warm gooey chocolate brownie", "calories": 380},
    {"name": "NY Cheesecake", "price": 280, "category": "desserts",
     "image": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=400",
     "emoji": "🍰", "is_veg": True, "trending": True,
     "description": "Creamy New York style", "calories": 450},
    {"name": "Gelato Trio", "price": 220, "category": "desserts",
     "image": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400",
     "emoji": "🍨", "is_veg": True, "trending": False,
     "description": "Three artisan gelato scoops", "calories": 320},
    # Drinks
    {"name": "Berry Mojito", "price": 180, "category": "drinks",
     "image": "https://images.unsplash.com/photo-1551538827-9c037cb4f32a?w=400",
     "emoji": "🍹", "is_veg": True, "trending": False,
     "description": "Refreshing berry mint cooler", "calories": 120},
    {"name": "Fresh Lemonade", "price": 120, "category": "drinks",
     "image": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400",
     "emoji": "🍋", "is_veg": True, "trending": False,
     "description": "Tangy homemade lemonade", "calories": 90},
    {"name": "Mango Tango", "price": 160, "category": "drinks",
     "image": "https://images.unsplash.com/photo-1623065422902-30a2d299bbe4?w=400",
     "emoji": "🥭", "is_veg": True, "trending": True,
     "description": "Tropical mango smoothie", "calories": 180},
    # Snacks
    {"name": "French Fries", "price": 120, "category": "snacks",
     "image": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400",
     "emoji": "🍟", "is_veg": True, "trending": False,
     "description": "Crispy golden fries", "calories": 320},
    {"name": "Loaded Nachos", "price": 220, "category": "snacks",
     "image": "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=400",
     "emoji": "🌮", "is_veg": True, "trending": True,
     "description": "Cheese salsa loaded nachos", "calories": 480},
    {"name": "Chicken Wings", "price": 280, "category": "snacks",
     "image": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400",
     "emoji": "🍗", "is_veg": False, "trending": False,
     "description": "Spicy buffalo wings", "calories": 420},
    {"name": "Paneer Tikka", "price": 260, "category": "snacks",
     "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=400",
     "emoji": "🧀", "is_veg": True, "trending": False,
     "description": "Grilled cottage cheese", "calories": 280},
    # Mains
    {"name": "Butter Chicken", "price": 380, "category": "mains",
     "image": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400",
     "emoji": "🍛", "is_veg": False, "trending": True,
     "description": "Creamy tomato chicken curry", "calories": 490},
    {"name": "Paneer Butter Masala", "price": 340, "category": "mains",
     "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400",
     "emoji": "🧀", "is_veg": True, "trending": False,
     "description": "Rich paneer in butter gravy", "calories": 420},
    {"name": "Veg Biryani", "price": 280, "category": "mains",
     "image": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400",
     "emoji": "🍚", "is_veg": True, "trending": False,
     "description": "Aromatic spiced rice", "calories": 380},
    {"name": "Chicken Biryani", "price": 350, "category": "mains",
     "image": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400",
     "emoji": "🍗", "is_veg": False, "trending": True,
     "description": "Hyderabadi dum biryani", "calories": 520},
]


class Command(BaseCommand):
    help = 'Seed the database with # SK cafe menu items and default settings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing menu items before seeding.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = MenuItem.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing menu items.'))

        created_count = 0
        for data in MENU_ITEMS:
            _, created = MenuItem.objects.get_or_create(
                name=data['name'],
                defaults={k: v for k, v in data.items() if k != 'name'},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅  Seeded {created_count} new menu items ({len(MENU_ITEMS) - created_count} already existed).'
        ))

        # Ensure default cafe settings exist
        settings, created = CafeSettings.objects.get_or_create(pk=1)
        action = 'Created' if created else 'Verified'
        self.stdout.write(self.style.SUCCESS(f'✅  {action} default CafeSettings.'))

        # Also seed tables
        from django.core.management import call_command
        call_command('seed_tables', stdout=self.stdout, stderr=self.stderr)
