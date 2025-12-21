from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile


class Command(BaseCommand):
    help = 'Creates a hardcoded admin user with username "admin" and password "admin"'

    def handle(self, *args, **kwargs):
        username = 'admin'
        password = 'admin'

        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists. Updating password...')
            )
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

            # Ensure the user has admin role
            if hasattr(user, 'profile'):
                user.profile.role = 'admin'
                user.profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Admin user "{username}" password updated and role set to admin.')
                )
            else:
                Profile.objects.create(user=user, role='admin')
                self.stdout.write(
                    self.style.SUCCESS(f'Admin user "{username}" password updated and profile created with admin role.')
                )
        else:
            # Create new admin user
            user = User.objects.create_user(
                username=username,
                password=password
            )

            # Set admin role in profile
            # The profile is automatically created by the post_save signal,
            # but we need to update the role to admin
            user.profile.role = 'admin'
            user.profile.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}" with password "{password}"')
            )
