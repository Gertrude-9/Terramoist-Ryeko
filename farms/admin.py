# # farms/admin.py
# from django.contrib import admin
# from fields.models import Farm, Field, Sensor

# class FieldInline(admin.TabularInline):
#     model = Field
#     extra = 1
#     show_change_link = True

# class SensorInline(admin.TabularInline):
#     model = Sensor
#     extra = 1

# # @admin.register(Farm)
# # class FarmAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'owner', 'location', 'created_at')
# #     list_filter = ('owner', 'created_at')
# #     search_fields = ('name', 'location')
# #     inlines = [FieldInline]

# # @admin.register(Field)
# # class FieldAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'farm', 'area', 'crop_type', 'soil_type')
# #     list_filter = ('farm', 'soil_type', 'crop_type')
# #     search_fields = ('name', 'farm__name')
# #     inlines = [SensorInline]

# # @admin.register(Sensor)
# # class SensorAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'sensor_type', 'field', 'is_active')
# #     list_filter = ('sensor_type', 'is_active', 'field__farm')
# #     search_fields = ('name', 'field__name', 'device_id')