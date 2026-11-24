from rest_framework.routers import SimpleRouter

from .views import DepoimentoViewSet

router = SimpleRouter(trailing_slash=False)
router.register("depoimentos", DepoimentoViewSet, basename="depoimentos")

urlpatterns = router.urls
