import os
from django.core.management.base import BaseCommand
from django.core.files import File
from reader.models import Story  # Your Story model import path

class Command(BaseCommand):
    help = 'Add images to Story model'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        image_dir = os.path.join(base_dir, 'static', 'images', 'thumbnail')
        image_files = os.listdir(image_dir)

        for image_file in image_files:
            if image_file.endswith('.jpg'):
                match = image_file.split('.')[0]
                try:
                    story_id = int(match)
                except ValueError:
                    print(f'Filename {image_file} does not start with a valid story ID')
                    continue

                try:
                    story = Story.objects.get(id=story_id)
                    # if story.image:
                    #     print(f'Story ID {story_id} already has an image. Skipping...')
                    #     continue

                    image_path = os.path.join(image_dir, image_file)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            story.image.save(f'{story_id}.jpg', File(img_file), save=True)
                            print(f'Successfully added image {image_file} to Story ID {story_id}')
                    else:
                        print(f'Image {image_file} not found')
                except Story.DoesNotExist:
                    print(f'Story with ID {story_id} does not exist')
            else:
                print(f'Filename {image_file} does not end with .jpg')
