from django.core.management.base import BaseCommand
from Hostels.models import Hostel, Room

class Command(BaseCommand):
    help = 'Creates hostel data with single, double, and 4-sharing rooms, 10 rooms per floor'

    def handle(self, *args, **kwargs):
        # Delete existing data
        Hostel.objects.all().delete()
        Room.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing hostel and room data'))

        hostels_data = [
            {
                'name': "IIT Delhi - Nilgiri Hall",
                'total_floors': 10,
                'features': "Lush Green Campus, 24/7 Library, Smart IoT Rooms, High-End Cafeteria, Tech Innovation Hub",
                'main_image': 'elite_hostel_room.png'
            },
            {
                'name': "IIT Bombay - Hostel 16",
                'total_floors': 8,
                'features': "Lake-View Rooms, Gigabit Fiber Internet, Private Gymnasium, Advanced Security Systems, Organic Mess",
                'main_image': 'elite_hostel_dining.png'
            },
            {
                'name': "NIT Surathkal - Mega Towers",
                'total_floors': 7,
                'features': "Private Beach Access, Rooftop Solar Power, Smart Lighting, 24/7 Medical Care, VR Gaming Lounge",
                'main_image': 'elite_campus_exterior.png'
            },
            {
                'name': "IIT Madras - Mandakini Hall",
                'total_floors': 9,
                'features': "Eco-Friendly Design, Research Collaborative Space, Gourmet Dining, Sports Arena, Smart Laundry",
                'main_image': 'elite_hostel_room.png'
            },
            {
                'name': "IIT Kanpur - Hall 12",
                'total_floors': 8,
                'features': "Aeronautical Lab Proximity, Quiet Study Zones, 24/7 Support, Solar Water Heating, Hi-Tech Common Room",
                'main_image': 'elite_hostel_dining.png'
            },
            {
                'name': "BITS Pilani - Budh Bhawan",
                'total_floors': 7,
                'features': "Serene Desert Landscape, World-Class Library, Tech Incubation Center, Smart Room Control, Premium Mess",
                'main_image': 'elite_campus_exterior.png'
            },
            {
                'name': "IIT Kharagpur - RK Hall",
                'total_floors': 9,
                'features': "Historical Heritage, Modern Interior, Fast Track Internet, Advanced Sports Complex, Tech Workshop",
                'main_image': 'elite_hostel_room.png'
            }
        ]

        for hostel_data in hostels_data:
            hostel = Hostel.objects.create(
                name=hostel_data['name'],
                total_floors=hostel_data['total_floors'],
                main_image=hostel_data['main_image'],
                features=hostel_data['features']
            )

            # Create 10 rooms per floor (4 singles, 3 doubles, 3 four-sharings)
            for floor in range(1, hostel.total_floors + 1):
                # Single Rooms (4 instances)
                for i in range(1, 5):  # Rooms 01 to 04
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 701, 702, 703, 704
                        room_type='single',
                        ac_type='ac' if i % 2 == 0 else 'non_ac',  # Alternate AC and non-AC
                        total_beds=1,
                        price=15000 if i % 2 == 0 else 12000,  # Higher for AC
                        amenities="Private Bathroom, Work Desk, WiFi, " +
                                  ("AC, Smart TV" if i % 2 == 0 else "Fan, LED Lighting")
                    )
                
                # Double Rooms (3 instances)
                for i in range(5, 8):  # Rooms 05 to 07
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 705, 706, 707
                        room_type='double',
                        ac_type='ac' if (i - 4) % 2 == 0 else 'non_ac',  # Alternate AC and non-AC
                        total_beds=2,
                        price=9000 if (i - 4) % 2 == 0 else 7000,  # Higher for AC
                        amenities="Shared Desk, Wardrobe, WiFi, " +
                                  ("AC" if (i - 4) % 2 == 0 else "Fan")
                    )
                
                # 4-Sharing Rooms (3 instances)
                for i in range(8, 11):  # Rooms 08 to 10
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 708, 709, 710
                        room_type='four',
                        ac_type='non_ac' if (i - 7) % 2 == 0 else 'ac',  # Alternate AC and non-AC
                        total_beds=4,
                        price=5000 if (i - 7) % 2 == 0 else 6000,  # Higher for AC
                        amenities="Bunk Beds, Shared Area, WiFi, " +
                                  ("AC" if (i - 7) % 2 == 0 else "Fan")
                    )

            self.stdout.write(self.style.SUCCESS(f'Created {hostel.name} with 10 rooms per floor across {hostel.total_floors} floors'))
