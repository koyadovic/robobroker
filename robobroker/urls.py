"""robobroker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from shared.domain.configurations import AbstractConfigurationStorage
from shared.domain.dependencies import dependency_dispatcher
from shared.domain.interfaces.environment import AbstractEnvironment
from shared.infrastructure.django_configurations import DjangoConfigurationStorage
from shared.infrastructure.django_environment import DjangoEnvironment
from trading.domain.interfaces import ICryptoCurrencySource, ILocalStorage
from trading.infrastructure.coinbase import CoinbaseCryptoCurrencySource
from trading.infrastructure.django_storage import DjangoLocalStorage

urlpatterns = [
    path('admin/', admin.site.urls),
]

dependency_dispatcher.register_implementation(AbstractEnvironment, DjangoEnvironment())
dependency_dispatcher.register_implementation(AbstractConfigurationStorage, DjangoConfigurationStorage())
dependency_dispatcher.register_implementation(ICryptoCurrencySource,
                                              CoinbaseCryptoCurrencySource(native_currency='EUR'))
dependency_dispatcher.register_implementation(ILocalStorage, DjangoLocalStorage())
