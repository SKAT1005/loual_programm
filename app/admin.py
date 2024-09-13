from django.contrib import admin

from app.models import User, Product, Lottery, Bonus, Rank, Category, Stocks


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Stocks)
class StocksAdmin(admin.ModelAdmin):
    pass

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    pass


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'unit']

@admin.register(Lottery)
class LotteryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
