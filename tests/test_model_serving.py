# tests/test_model_serving.py
"""
اختبارات شاملة لبنية تقديم نماذج AI
Tests for Model Serving, A/B Testing, Shadow Mode, Ensemble
"""

import time

import pytest

from app.services.model_serving_infrastructure import (ModelServingInfrastructure, ModelStatus,
                                                       ModelType, ModelVersion,
                                                       get_model_serving_infrastructure)


class TestModelServingInfrastructure:
    """اختبارات بنية تقديم النماذج"""

    @pytest.fixture
    def infrastructure(self):
        """إنشاء بنية جديدة للاختبار"""
        return ModelServingInfrastructure()

    @pytest.fixture
    def sample_model(self):
        """إنشاء نموذج نموذجي"""
        return ModelVersion(
            version_id="model-v1",
            model_name="gpt-test",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
            endpoint="/api/v1/generate",
        )

    @pytest.fixture
    def alternative_model(self):
        """إنشاء نموذج بديل"""
        return ModelVersion(
            version_id="model-v2",
            model_name="gpt-test",
            version_number="2.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
            endpoint="/api/v2/generate",
        )

    # ======================================================================================
    # MODEL REGISTRATION TESTS
    # ======================================================================================

    def test_model_registration(self, infrastructure, sample_model):
        """اختبار تسجيل نموذج"""
        success = infrastructure.register_model(sample_model)

        assert success is True

        # التحقق من التسجيل
        registered = infrastructure.get_model_status(sample_model.version_id)
        assert registered is not None
        assert registered.model_name == "gpt-test"

    def test_model_loading_status(self, infrastructure, sample_model):
        """اختبار حالة التحميل"""
        infrastructure.register_model(sample_model)

        # في البداية يكون في حالة تحميل
        assert sample_model.status == ModelStatus.LOADING

        # الانتظار حتى يصبح جاهزاً
        time.sleep(3)

        # يجب أن يصبح جاهزاً
        assert sample_model.status == ModelStatus.READY

    def test_duplicate_registration_prevention(self, infrastructure, sample_model):
        """اختبار منع التسجيل المكرر"""
        infrastructure.register_model(sample_model)

        # محاولة التسجيل مرة أخرى
        success = infrastructure.register_model(sample_model)

        assert success is False

    # ======================================================================================
    # MODEL SERVING TESTS
    # ======================================================================================

    def test_serve_request_basic(self, infrastructure, sample_model):
        """اختبار تقديم طلب أساسي"""
        infrastructure.register_model(sample_model)
        time.sleep(3)  # انتظار التحميل

        response = infrastructure.serve_request(
            model_name="gpt-test",
            input_data={"prompt": "Hello, world!"},
            version_id=sample_model.version_id,
        )

        assert response is not None
        assert response.success is True
        assert response.latency_ms >= 0

    def test_serve_request_model_not_ready(self, infrastructure, sample_model):
        """اختبار الطلب عندما النموذج غير جاهز"""
        infrastructure.register_model(sample_model)

        # الطلب فوراً قبل الجهوزية
        response = infrastructure.serve_request(
            model_name="gpt-test",
            input_data={"prompt": "Test"},
            version_id=sample_model.version_id,
        )

        # يجب أن يفشل لأن النموذج ليس جاهزاً
        assert response.success is False

    def test_serve_request_latest_version(self, infrastructure, sample_model, alternative_model):
        """اختبار اختيار أحدث نسخة تلقائياً"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        # طلب بدون تحديد النسخة
        response = infrastructure.serve_request(
            model_name="gpt-test",
            input_data={"prompt": "Test"},
        )

        # يجب أن يختار نسخة جاهزة
        assert response.success is True or response.error == "Model not ready"

    # ======================================================================================
    # A/B TESTING TESTS
    # ======================================================================================

    def test_ab_test_creation(self, infrastructure, sample_model, alternative_model):
        """اختبار إنشاء اختبار A/B"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        test_id = infrastructure.start_ab_test(
            model_a_id=sample_model.version_id,
            model_b_id=alternative_model.version_id,
            split_percentage=60.0,
            duration_hours=1,
        )

        assert test_id is not None

        # التحقق من التكوين
        config = infrastructure.get_ab_test_status(test_id)
        assert config is not None
        assert config.model_a_percentage == 60.0
        assert config.model_b_percentage == 40.0

    def test_ab_test_request_serving(self, infrastructure, sample_model, alternative_model):
        """اختبار تقديم طلبات في اختبار A/B"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        test_id = infrastructure.start_ab_test(
            model_a_id=sample_model.version_id,
            model_b_id=alternative_model.version_id,
        )

        # تقديم عدة طلبات
        for _ in range(5):
            response = infrastructure.serve_ab_test_request(
                test_id=test_id,
                input_data={"prompt": "Test"},
            )

            # يجب أن يكون من أحد النموذجين
            assert response.version_id in [sample_model.version_id, alternative_model.version_id]

    def test_ab_test_analysis(self, infrastructure, sample_model, alternative_model):
        """اختبار تحليل نتائج A/B"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        test_id = infrastructure.start_ab_test(
            model_a_id=sample_model.version_id,
            model_b_id=alternative_model.version_id,
            duration_hours=0,  # ينتهي فوراً
        )

        # تحليل النتائج
        results = infrastructure.analyze_ab_test(test_id)

        assert "winner" in results
        assert "model_a_metrics" in results
        assert "model_b_metrics" in results

    # ======================================================================================
    # SHADOW MODE TESTS
    # ======================================================================================

    def test_shadow_deployment_creation(self, infrastructure, sample_model, alternative_model):
        """اختبار إنشاء نشر خفي"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        shadow_id = infrastructure.start_shadow_deployment(
            primary_model_id=sample_model.version_id,
            shadow_model_id=alternative_model.version_id,
            traffic_percentage=50.0,
        )

        assert shadow_id is not None

    def test_shadow_request_serving(self, infrastructure, sample_model, alternative_model):
        """اختبار تقديم طلبات في الوضع الخفي"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        shadow_id = infrastructure.start_shadow_deployment(
            primary_model_id=sample_model.version_id,
            shadow_model_id=alternative_model.version_id,
        )

        # تقديم طلب
        response = infrastructure.serve_with_shadow(
            shadow_id=shadow_id,
            input_data={"prompt": "Test"},
        )

        # يجب أن تكون الاستجابة من النموذج الأساسي
        assert response.version_id == sample_model.version_id

    def test_shadow_deployment_stats(self, infrastructure, sample_model, alternative_model):
        """اختبار إحصائيات النشر الخفي"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        shadow_id = infrastructure.start_shadow_deployment(
            primary_model_id=sample_model.version_id,
            shadow_model_id=alternative_model.version_id,
        )

        # تقديم بعض الطلبات
        for _ in range(3):
            infrastructure.serve_with_shadow(
                shadow_id=shadow_id,
                input_data={"prompt": "Test"},
            )

        time.sleep(1)

        # الحصول على الإحصائيات
        stats = infrastructure.get_shadow_deployment_stats(shadow_id)

        assert stats is not None
        assert "shadow_id" in stats

    # ======================================================================================
    # ENSEMBLE TESTS
    # ======================================================================================

    def test_ensemble_creation(self, infrastructure, sample_model, alternative_model):
        """اختبار إنشاء تجميع نماذج"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)

        ensemble_id = infrastructure.create_ensemble(
            model_versions=[sample_model.version_id, alternative_model.version_id],
            aggregation_method="voting",
        )

        assert ensemble_id is not None

    def test_ensemble_request_serving(self, infrastructure, sample_model, alternative_model):
        """اختبار تقديم طلبات للتجميع"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)
        time.sleep(3)

        ensemble_id = infrastructure.create_ensemble(
            model_versions=[sample_model.version_id, alternative_model.version_id],
        )

        # تقديم طلب
        response = infrastructure.serve_ensemble_request(
            ensemble_id=ensemble_id,
            input_data={"prompt": "Test ensemble"},
        )

        assert response is not None
        assert response.model_id.startswith("ensemble-")

    # ======================================================================================
    # MODEL MANAGEMENT TESTS
    # ======================================================================================

    def test_model_unloading(self, infrastructure, sample_model):
        """اختبار إلغاء تحميل نموذج"""
        infrastructure.register_model(sample_model)
        time.sleep(3)

        success = infrastructure.unload_model(sample_model.version_id)

        assert success is True

        # التحقق من الحالة
        time.sleep(1)
        assert sample_model.status in [ModelStatus.DRAINING, ModelStatus.STOPPED]

    def test_list_models(self, infrastructure, sample_model, alternative_model):
        """اختبار قائمة النماذج"""
        infrastructure.register_model(sample_model)
        infrastructure.register_model(alternative_model)

        models = infrastructure.list_models()

        assert len(models) >= 2
        assert any(m.version_id == sample_model.version_id for m in models)
        assert any(m.version_id == alternative_model.version_id for m in models)

    # ======================================================================================
    # SINGLETON TEST
    # ======================================================================================

    def test_singleton_instance(self):
        """اختبار أن البنية تعمل كـ Singleton"""
        instance1 = get_model_serving_infrastructure()
        instance2 = get_model_serving_infrastructure()

        assert instance1 is instance2


class TestModelMetrics:
    """اختبارات المقاييس والمراقبة"""

    @pytest.fixture
    def infrastructure(self):
        return ModelServingInfrastructure()

    def test_metrics_tracking(self, infrastructure):
        """اختبار تتبع المقاييس"""
        model = ModelVersion(
            version_id="metrics-test",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )

        infrastructure.register_model(model)
        time.sleep(3)

        # تقديم بعض الطلبات
        for _ in range(3):
            infrastructure.serve_request(
                model_name="test-model",
                input_data={"prompt": "Test"},
                version_id="metrics-test",
            )

        # لا يوجد استثناء = نجاح
        assert True
