#!/bin/bash
# =============================================================================
# CogniForge Services Cleanup Script
# =============================================================================
# هذا السكريبت يقوم بحذف الخدمات غير المستخدمة والمكررة بشكل آمن
# 
# الاستخدام:
#   ./scripts/cleanup_services.sh --dry-run    # معاينة فقط
#   ./scripts/cleanup_services.sh --execute    # تنفيذ فعلي
#
# =============================================================================

set -e  # إيقاف عند أول خطأ

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# المتغيرات
DRY_RUN=true
SERVICES_DIR="app/services"
BACKUP_DIR="backup/services_$(date +%Y%m%d_%H%M%S)"

# معالجة المعاملات
if [ "$1" == "--execute" ]; then
    DRY_RUN=false
    echo -e "${RED}⚠️  تحذير: سيتم حذف الملفات فعلياً!${NC}"
    read -p "هل أنت متأكد؟ (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "تم الإلغاء."
        exit 0
    fi
elif [ "$1" == "--dry-run" ] || [ -z "$1" ]; then
    DRY_RUN=true
    echo -e "${BLUE}ℹ️  وضع المعاينة - لن يتم حذف أي ملفات${NC}"
else
    echo "الاستخدام: $0 [--dry-run|--execute]"
    exit 1
fi

# دالة للحذف الآمن
safe_delete() {
    local path="$1"
    local reason="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[معاينة]${NC} سيتم حذف: $path ($reason)"
    else
        if [ -e "$path" ]; then
            echo -e "${RED}[حذف]${NC} $path ($reason)"
            rm -rf "$path"
        else
            echo -e "${YELLOW}[تخطي]${NC} $path (غير موجود)"
        fi
    fi
}

# إنشاء نسخة احتياطية
if [ "$DRY_RUN" = false ]; then
    echo -e "${GREEN}📦 إنشاء نسخة احتياطية...${NC}"
    mkdir -p "$BACKUP_DIR"
    cp -r "$SERVICES_DIR" "$BACKUP_DIR/"
    echo -e "${GREEN}✅ تم حفظ النسخة الاحتياطية في: $BACKUP_DIR${NC}"
fi

echo ""
echo "============================================================================="
echo "المرحلة 1: حذف الخدمات غير المستخدمة (27 خدمة)"
echo "============================================================================="

# الخدمات غير المستخدمة
safe_delete "$SERVICES_DIR/adaptive" "غير مستخدم"
safe_delete "$SERVICES_DIR/admin_ai_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/admin_chat_performance" "غير مستخدم"
safe_delete "$SERVICES_DIR/admin_chat_performance_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/advanced_streaming" "غير مستخدم"
safe_delete "$SERVICES_DIR/advanced_streaming_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/ai_model_metrics_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/ai_project_management" "غير مستخدم"
safe_delete "$SERVICES_DIR/ai_testing" "غير مستخدم"
safe_delete "$SERVICES_DIR/aiops" "غير مستخدم"
safe_delete "$SERVICES_DIR/api_event_driven_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/async_tool_bridge.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/chaos_engineering.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/distributed_tracing.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/domain_events.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/execution" "غير مستخدم"
safe_delete "$SERVICES_DIR/fastapi_generation_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/horizontal_scaling_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/infrastructure_metrics_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/master_agent" "غير مستخدم"
safe_delete "$SERVICES_DIR/metrics" "غير مستخدم"
safe_delete "$SERVICES_DIR/micro_frontends_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/multi_layer_cache_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/user_analytics_metrics_service.py" "غير مستخدم"
safe_delete "$SERVICES_DIR/ensemble_ai.py" "تجريبي غير مستخدم"
safe_delete "$SERVICES_DIR/breakthrough_streaming.py" "تجريبي غير مستخدم"
safe_delete "$SERVICES_DIR/duplication_buster.py" "أداة غير مستخدمة"

echo ""
echo "============================================================================="
echo "المرحلة 2: حذف Wrappers والملفات المكررة"
echo "============================================================================="

# Wrappers
safe_delete "$SERVICES_DIR/auth_boundary_service.py" "wrapper - استخدم auth_boundary/"
safe_delete "$SERVICES_DIR/project_context_service.py" "wrapper - استخدم project_context/"
safe_delete "$SERVICES_DIR/data_mesh_service.py" "wrapper - استخدم data_mesh/"
safe_delete "$SERVICES_DIR/api_contract_service.py" "placeholder فارغ"
safe_delete "$SERVICES_DIR/api_governance_service.py" "wrapper"
safe_delete "$SERVICES_DIR/api_security_service.py" "wrapper"

# Shim files
safe_delete "$SERVICES_DIR/ai_adaptive_microservices.py" "shim - استخدم adaptive/"
safe_delete "$SERVICES_DIR/ai_advanced_security.py" "shim - استخدم ai_security/"
safe_delete "$SERVICES_DIR/ai_intelligent_testing.py" "shim - استخدم ai_testing/"

echo ""
echo "============================================================================="
echo "المرحلة 3: حذف الخدمات المكررة (سيتم دمجها لاحقاً)"
echo "============================================================================="

# Chat duplicates
safe_delete "$SERVICES_DIR/admin_chat_streaming" "مكرر - دمج في chat/"
safe_delete "$SERVICES_DIR/admin_chat_streaming_service.py" "مكرر - دمج في chat/"
safe_delete "$SERVICES_DIR/chat_orchestrator_service.py" "مكرر - دمج في chat/"

# LLM duplicates
safe_delete "$SERVICES_DIR/llm_client" "مكرر - دمج في llm/"
safe_delete "$SERVICES_DIR/llm_client_service.py" "مكرر - دمج في llm/"

# CRUD duplicates
safe_delete "$SERVICES_DIR/crud_boundary" "مكرر - دمج في crud/"
safe_delete "$SERVICES_DIR/crud_boundary_service.py" "مكرر - دمج في crud/"

# Security duplicates
safe_delete "$SERVICES_DIR/ai_security" "مكرر - دمج في security/"
safe_delete "$SERVICES_DIR/security_metrics" "مكرر - دمج في security/"

# Orchestration duplicates
safe_delete "$SERVICES_DIR/saga_orchestrator.py" "مكرر - دمج في orchestration/"

echo ""
echo "============================================================================="
echo "📊 ملخص العملية"
echo "============================================================================="

if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}ℹ️  هذه معاينة فقط. لم يتم حذف أي ملفات.${NC}"
    echo -e "${GREEN}✅ لتنفيذ الحذف الفعلي، استخدم: $0 --execute${NC}"
else
    echo -e "${GREEN}✅ تم حذف الخدمات غير المستخدمة والمكررة${NC}"
    echo -e "${GREEN}📦 النسخة الاحتياطية: $BACKUP_DIR${NC}"
    echo ""
    echo "الخطوات التالية:"
    echo "1. تشغيل الاختبارات: pytest"
    echo "2. التحقق من عمل API: make test-api"
    echo "3. إذا كان هناك مشاكل، استرجع من: $BACKUP_DIR"
fi

echo ""
echo "============================================================================="
echo "الخدمات المتبقية (15 خدمة أساسية):"
echo "============================================================================="
echo "✅ user_service.py"
echo "✅ system_service.py"
echo "✅ database_service.py"
echo "✅ history_service.py"
echo "✅ observability_boundary_service.py"
echo "✅ chat/"
echo "✅ llm/"
echo "✅ auth_boundary/"
echo "✅ security/"
echo "✅ crud/"
echo "✅ agent_tools/"
echo "✅ project_context/"
echo "✅ orchestration/"
echo "✅ resilience/"
echo "✅ serving/"
echo ""
echo "⚠️  ملاحظة: overmind/ و data_mesh/ تحتاج تبسيط (مرحلة لاحقة)"
echo ""
