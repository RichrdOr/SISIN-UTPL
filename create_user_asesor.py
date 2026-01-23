from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario

email = 'MartaSegu@gmail.com'
password = 'Carl3$@5'
username = email

user, created = User.objects.get_or_create(username=username, defaults={'email': email})
if created:
    user.set_password(password)
    user.save()
    print('Usuario creado:', user.username)
else:
    # update password to known value
    user.set_password(password)
    user.email = email
    user.save()
    print('Usuario actualizado:', user.username)

perfil, pcreated = PerfilUsuario.objects.get_or_create(user=user, defaults={'rol': 'asesor'})
if not pcreated:
    perfil.rol = 'asesor'
    perfil.save()
    print('Perfil actualizado a asesor')
else:
    print('Perfil creado con rol asesor')

print('Listo. Puedes iniciar sesión con:', email, password)
