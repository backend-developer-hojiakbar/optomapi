from rest_framework import permissions


class HasPermission(permissions.BasePermission):
    """
    Foydalanuvchida ma'lum bir ruxsat borligini tekshiradi.
    Bu permission'dan foydalanadigan har bir view'da "required_permission" atributi bo'lishi kerak.
    """
    message = 'Sizda bu amalni bajarish uchun ruxsat yo`q.'

    def has_permission(self, request, view):
        # Foydalanuvchi tizimga kirganligini tekshirish
        if not request.user or not request.user.is_authenticated:
            return False

        # View'dan kerakli ruxsat nomini olish
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            # Agar dasturchi required_permission'ni view'ga qo'shmagan bo'lsa, bu xatolik.
            # Ruxsatni rad etamiz.
            return False

            # Foydalanuvchi rolida kerakli ruxsat borligini tekshirish
        if not hasattr(request.user, 'role') or not request.user.role:
            return False

        return required_permission in request.user.role.permissions