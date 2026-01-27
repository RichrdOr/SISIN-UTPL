from django.contrib.auth.decorators import user_passes_test

def check_asesora(user):
    return user.is_authenticated and (user.groups.filter(name='Asesora').exists() or user.is_superuser)

def check_gerente(user):
    return user.is_authenticated and (user.groups.filter(name='Gerente').exists() or user.is_superuser)

def asesora_required(view_func):
    return user_passes_test(check_asesora, login_url='login')(view_func)

def gerente_required(view_func):
    return user_passes_test(check_gerente, login_url='login')(view_func)