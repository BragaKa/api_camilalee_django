from rest_framework.routers import SimpleRouter

from .views import MensagemViewSet

router = SimpleRouter(trailing_slash=False)
router.register("mensagens", MensagemViewSet, basename="mensagens")

urlpatterns = router.urls
