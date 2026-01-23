from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear usuarios iniciales para el sistema'

    def handle(self, *args, **options):
        # Crear usuario Gerente
        if not User.objects.filter(username='NancyS@utpl.edu.ec').exists():
            gerente = User.objects.create_user(
                username='NancyS@utpl.edu.ec',
                email='NancyS@utpl.edu.ec',
                password='Nncy$/23',
                first_name='Nancy',
                last_name='S',
                rol='gerente'
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Usuario Gerente creado: NancyS@utpl.edu.ec')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  El usuario Gerente ya existe')
            )

        # Crear usuario Asesor
        if not User.objects.filter(username='MartaSeguro@gmail.com').exists():
            asesor = User.objects.create_user(
                username='MartaSeguro@gmail.com',
                email='MartaSeguro@gmail.com',
                password='Carl3$@5',
                first_name='Marta',
                last_name='Seguro',
                rol='asesor'
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Usuario Asesor creado: MartaSeguro@gmail.com')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  El usuario Asesor ya existe')
            )

        self.stdout.write(
            self.style.SUCCESS('🎉 Usuarios creados exitosamente!')
        )
