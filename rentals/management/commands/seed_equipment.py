import os
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from rentals.models import Category, Equipment, EquipmentImage

PLACEHOLDER_DIR = os.path.join(os.path.dirname(__file__), 'seed_images')

# (category key, category display name)
CATEGORIES = {
    'cameras': 'Cameras',
    'lenses': 'Lenses',
    'lighting': 'Lighting',
    'audio': 'Audio',
    'support': 'Tripods & Support',
    'drones': 'Drones',
    'accessories': 'Accessories',
}

# (name, daily_rate, category_key, description)
EQUIPMENT = [
    ("Canon RF 24-70mm f/2.8L IS USM", 1200, 'lenses', "Pro standard zoom with image stabilization — the workhorse lens for events, portraits, and run-and-gun video."),
    ("Sony FE 85mm f/1.4 GM", 900, 'lenses', "Fast portrait prime with buttery bokeh, ideal for headshots and cinematic close-ups."),
    ("Sigma 18-35mm f/1.8 Art (EF mount)", 700, 'lenses', "Constant f/1.8 wide-angle zoom, a favorite for interiors, vlogging, and low-light run-and-gun."),

    ("Aputure 120D II LED Light", 1000, 'lighting', "Daylight-balanced LED with Bowens mount, bright enough to key a full scene."),
    ("Godox AD200Pro Flash Kit (w/ softbox)", 800, 'lighting', "Portable strobe kit with softbox included — location-friendly power in a small bag."),

    ("Rode VideoMic Pro+", 350, 'audio', "On-camera shotgun mic with internal battery and auto power-save, for clean run-and-gun audio."),
    ("Zoom H6 Portable Audio Recorder", 450, 'audio', "6-track field recorder with swappable capsules, for interviews and multi-source audio."),

    ("Manfrotto MT055XPRO3 Tripod + Head", 300, 'support', "Sturdy aluminum tripod with fluid-friendly head, the everyday stability choice."),
    ("DJI RS 3 Mini Gimbal Stabilizer", 600, 'support', "Compact 3-axis gimbal for smooth handheld motion on mirrorless bodies."),
    ("Neewer Camera Slider (100cm, motorized)", 500, 'support', "Motorized slider for controlled, repeatable dolly moves."),

    ("DJI Mini 4 Pro", 1500, 'drones', "Sub-249g drone with 4K/60fps HDR video and omnidirectional obstacle sensing."),
    ("DJI Air 3", 2200, 'drones', "Dual-camera drone (wide + tele) with 46-minute flight time for serious aerial work."),

    ("SanDisk Extreme Pro 128GB SD Card", 100, 'accessories', "High-speed UHS-I card, keeps up with 4K burst shooting."),
    ("Spare Camera Battery (LP-E6NH type)", 100, 'accessories', "Extra battery so a full day of shooting never gets cut short."),
    ("Variable ND Filter (77mm)", 150, 'accessories', "Adjustable 2-5 stop ND for controlling exposure in bright daylight video."),
    ("Camera Backpack (Lowepro ProTactic)", 200, 'accessories', "Padded, weather-resistant bag for safely hauling a full kit."),
    ("Portable LED Ring Light w/ Stand", 250, 'accessories', "Compact ring light for vlogging, interviews, and product shots."),
]


class Command(BaseCommand):
    help = "Seeds starter categories, equipment, and branded placeholder images for klick.cebu."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help="Delete existing seeded equipment/categories before reseeding."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            Equipment.objects.filter(name__in=[e[0] for e in EQUIPMENT]).delete()
            Category.objects.filter(name__in=CATEGORIES.values()).delete()
            self.stdout.write(self.style.WARNING("Cleared previously seeded categories/equipment."))

        cat_objs = {}
        for key, display in CATEGORIES.items():
            cat, created = Category.objects.get_or_create(name=display)
            cat_objs[key] = cat
            if created:
                self.stdout.write(f"Created category: {display}")

        created_count = 0
        for name, rate, cat_key, description in EQUIPMENT:
            equipment, created = Equipment.objects.get_or_create(
                name=name,
                defaults={
                    'daily_rate': rate,
                    'description': description,
                    'condition': 'excellent',
                    'is_available': True,
                },
            )
            if not created:
                continue
            created_count += 1
            equipment.categories.add(cat_objs[cat_key])

            image_path = os.path.join(PLACEHOLDER_DIR, f'{cat_key}.png')
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    equipment.images.create(
                        image=File(f, name=f'{cat_key}-placeholder.png'),
                        is_primary=True,
                    )
            self.stdout.write(f"  + {name} (₱{rate}/day) -> {CATEGORIES[cat_key]}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} equipment item(s) created, {len(CATEGORIES)} categories ensured."
        ))
