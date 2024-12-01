from django.contrib import admin
from .models import Wrap, WrapCounter, UserWrappedHistory

admin.site.register(Wrap)
admin.site.register(WrapCounter)
admin.site.register(UserWrappedHistory)