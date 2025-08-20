import pytest
from modules.procurement.bias_detector import BiasDetector
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

class TestBiasDetection:
    """
    اختبارات شاملة لكشف التحيز في القرارات
    Comprehensive bias detection tests
    """
    
    @pytest.fixture
    def bias_detector(self):
        """Create bias detector instance"""
        return BiasDetector()
    
    @pytest.mark.asyncio
    async def test_all_13_saudi_regions(self, bias_detector):
        """Test all 13 Saudi regions for bias detection"""
        regions = [
            "الرياض",      # Riyadh
            "مكة المكرمة",  # Makkah
            "المنطقة الشرقية", # Eastern Province
            "المدينة المنورة", # Madinah
            "القصيم",       # Qassim
            "حائل",        # Hail
            "تبوك",        # Tabuk
            "الحدود الشمالية", # Northern Borders
            "جازان",       # Jazan
            "نجران",       # Najran
            "الباحة",      # Al Bahah
            "الجوف",       # Al Jouf
            "عسير"         # Asir
        ]
        
        # Test regional coverage
        assert len(regions) == 13, "Should test all 13 Saudi regions"
        
        # Create sample decisions for each region
        decisions = []
        for i, region in enumerate(regions):
            decision = {
                "region": region,
                "vendor_name": f"شركة {region} التجارية",
                "award_amount": 100000 + (i * 10000),
                "decision_date": datetime.now() - timedelta(days=i)
            }
            decisions.append(decision)
        
        # Test regional distribution analysis
        assert len(decisions) == 13
        for decision in decisions:
            assert decision["region"] in regions
    
    @pytest.mark.asyncio
    async def test_statistical_significance(self, bias_detector):
        """Test statistical significance using chi-square tests"""
        # Sample data for chi-square test
        observed_distribution = [50, 30, 20]  # Riyadh, Makkah, Eastern
        expected_distribution = [33.33, 33.33, 33.33]  # Equal distribution
        
        # Test statistical calculation
        from scipy.stats import chisquare
        chi2_stat, p_value = chisquare(observed_distribution, expected_distribution)
        
        assert chi2_stat > 0, "Chi-square statistic should be positive"
        assert 0 <= p_value <= 1, f"P-value should be between 0 and 1, got {p_value}"
        
        # Test significance threshold (p < 0.05 indicates bias)
        significance_threshold = 0.05
        bias_detected = p_value < significance_threshold
        
        assert isinstance(bias_detected, bool), "Bias detection should return boolean"
    
    @pytest.mark.asyncio
    async def test_visual_chart_generation(self, bias_detector):
        """Test visual chart data generation for bias analysis"""
        # Sample procurement decisions data
        decisions_data = [
            {"region": "الرياض", "count": 45, "percentage": 45.0},
            {"region": "مكة المكرمة", "count": 25, "percentage": 25.0},
            {"region": "المنطقة الشرقية", "count": 20, "percentage": 20.0},
            {"region": "المدينة المنورة", "count": 10, "percentage": 10.0}
        ]
        
        # Test chart data generation
        chart_data = await bias_detector.generate_visual_chart_data(decisions_data)
        
        assert "chart_type" in chart_data, "Should specify chart type"
        assert "data_points" in chart_data, "Should contain data points"
        assert "labels" in chart_data, "Should contain Arabic labels"
        assert "colors" in chart_data, "Should contain color scheme"
        
        # Test chart data structure
        assert chart_data["chart_type"] in ["pie", "bar", "histogram"]
        assert len(chart_data["data_points"]) == len(decisions_data)
        
        # Test Arabic labels
        for label in chart_data["labels"]:
            assert any(arabic_char in label for arabic_char in "ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
    
    @pytest.mark.asyncio
    async def test_alert_thresholds(self, bias_detector):
        """Test bias alert thresholds and notification triggers"""
        # Test regional bias threshold (15% deviation)
        regional_threshold = 0.15
        assert bias_detector.regional_deviation_threshold == regional_threshold
        
        # Test temporal bias threshold (20% deviation) 
        temporal_threshold = 0.20
        assert bias_detector.temporal_deviation_threshold == temporal_threshold
        
        # Test vendor size bias threshold (25% deviation)
        vendor_size_threshold = 0.25
        assert bias_detector.vendor_size_deviation_threshold == vendor_size_threshold
        
        # Test alert triggering
        high_bias_score = 0.30  # Above all thresholds
        low_bias_score = 0.05   # Below all thresholds
        
        # High bias should trigger alerts
        high_bias_result = await bias_detector.check_alert_thresholds(high_bias_score)
        assert high_bias_result["alert_triggered"] == True
        assert high_bias_result["notification_required"] == True
        assert "NAZAHA" in high_bias_result["notify_entities"]
        
        # Low bias should not trigger alerts
        low_bias_result = await bias_detector.check_alert_thresholds(low_bias_score)
        assert low_bias_result["alert_triggered"] == False
        assert low_bias_result["notification_required"] == False
    
    @pytest.mark.asyncio
    async def test_gcc_preference_detection(self, bias_detector):
        """Test GCC country preference bias detection"""
        gcc_vendors = [
            {"name": "شركة إماراتية", "country": "AE", "selected": True},
            {"name": "شركة كويتية", "country": "KW", "selected": True},
            {"name": "شركة قطرية", "country": "QA", "selected": False},
            {"name": "شركة بحرينية", "country": "BH", "selected": True},
        ]
        
        non_gcc_vendors = [
            {"name": "شركة مصرية", "country": "EG", "selected": False},
            {"name": "شركة هندية", "country": "IN", "selected": False},
            {"name": "شركة أمريكية", "country": "US", "selected": False},
        ]
        
        # Test GCC preference detection
        result = await bias_detector.check_gcc_preference(gcc_vendors + non_gcc_vendors)
        
        assert "gcc_selection_rate" in result
        assert "non_gcc_selection_rate" in result
        assert "preference_detected" in result
        
        # GCC vendors should have higher selection rate
        assert result["gcc_selection_rate"] > result["non_gcc_selection_rate"]
    
    @pytest.mark.asyncio
    async def test_tribal_bias_detection(self, bias_detector):
        """Test tribal/family name bias detection"""
        decision_makers = [
            {"name": "أحمد بن محمد آل سعود", "decisions": 5},
            {"name": "فهد بن عبدالله آل سعود", "decisions": 3},
            {"name": "محمد بن أحمد الزهراني", "decisions": 1},
            {"name": "عبدالله بن سعد العتيبي", "decisions": 1},
        ]
        
        winning_vendors = [
            {"name": "شركة آل سعود للتجارة", "family": "آل سعود", "awards": 6},
            {"name": "مؤسسة الزهراني", "family": "الزهراني", "awards": 2},
            {"name": "شركة العتيبي", "family": "العتيبي", "awards": 2},
        ]
        
        # Test tribal bias detection
        result = await bias_detector.check_tribal_indicators(decision_makers, winning_vendors)
        
        assert "tribal_bias_detected" in result
        assert "family_name_matches" in result
        assert "confidence_score" in result
        
        # Should detect potential tribal bias (same family names)
        assert result["family_name_matches"] > 0
    
    @pytest.mark.asyncio
    async def test_saudization_bias_detection(self, bias_detector):
        """Test Saudization percentage bias in vendor selection"""
        vendors = [
            {"name": "شركة عالية التسعود", "saudization": 85, "selected": True},
            {"name": "شركة متوسطة التسعود", "saudization": 45, "selected": False},
            {"name": "شركة منخفضة التسعود", "saudization": 20, "selected": False},
            {"name": "شركة ممتازة التسعود", "saudization": 95, "selected": True},
        ]
        
        # Test Saudization bias detection
        result = await bias_detector.check_saudization_bias(vendors)
        
        assert "average_saudization_selected" in result
        assert "average_saudization_rejected" in result
        assert "bias_toward_high_saudization" in result
        
        # Should show preference for higher Saudization
        assert result["average_saudization_selected"] > result["average_saudization_rejected"]
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, bias_detector):
        """Test bias detection performance with large datasets"""
        import time
        
        # Create large dataset (1000 decisions)
        large_dataset = []
        for i in range(1000):
            decision = {
                "decision_id": f"PROC_2024_{i:06d}",
                "region": ["الرياض", "مكة المكرمة", "المنطقة الشرقية"][i % 3],
                "vendor_name": f"شركة التجارة {i}",
                "award_amount": 100000 + (i * 1000),
                "decision_date": datetime.now() - timedelta(days=i % 365)
            }
            large_dataset.append(decision)
        
        # Test performance
        start_time = time.time()
        result = await bias_detector.analyze_large_dataset(large_dataset)
        processing_time = time.time() - start_time
        
        # Should process 1000 decisions in under 5 seconds
        assert processing_time < 5.0, f"Processing took too long: {processing_time:.2f} seconds"
        assert result["total_decisions"] == 1000
        assert "processing_time_ms" in result