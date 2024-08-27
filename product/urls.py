from django.urls import path
from .views import (
    ScanInfoView, CheckoutInfoView, PatchInfoView,
    ScanMetricsView, CheckoutMetricsView, TopLocationMetrics,
    PerformanceMetricsView,
    ProductAndUserMetricsView, 
    LineChartDataView, 
    BarChartDataView,
    )

urlpatterns = [
    path('qrinfo/', ScanInfoView.as_view(), name='qr_info'),
    path('checkoutinfo/', CheckoutInfoView.as_view(), name='checkout_info'),
    path('patchinfo/', PatchInfoView.as_view(), name='patch_info'),
    path('scanmetrics/', ScanMetricsView.as_view(), name='scan_metrics'),
    path('checkoutmetrics/', CheckoutMetricsView.as_view(), name='checkout_metrics'),
    path('toplocation/', TopLocationMetrics.as_view(), name='top_location'),
    path('performance/', PerformanceMetricsView.as_view(), name='performance_metrics'),
    path('cust/', ProductAndUserMetricsView.as_view(), name='customer_products'),
    path('lineChart/', LineChartDataView.as_view(), name='line_data'),
    path('barChart/', BarChartDataView.as_view(), name='bar_data'),
]
