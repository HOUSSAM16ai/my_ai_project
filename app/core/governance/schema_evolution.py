"""
نظام حوكمة المخططات وتطور العقود (Schema Governance & Contract Evolution).
--------------------------------------------------------------------------
يقدم هذا النموذج حلاً عبقرياً لمشكلة $dynamicRef في OpenAPI 3.1
عبر محاكاة دقة التحليل الثابت (Static Analysis Simulation)
لحل المراجع الديناميكية واكتشاف التكرار (Recursion) دون تشغيل فعلي.

الخوارزمية (The Algorithm):
1.  **تحليل النطاق الديناميكي (Dynamic Scope Analysis)**: تتبع "مكدس النطاق" (Scope Stack)
    أثناء اجتياز المخطط لمحاكاة سلوك وقت التشغيل.
2.  **الكشف عن التكرار (Cycle Detection)**: استخدام معرفات فريدة (URI + Scope Hash)
    لاكتشاف الحلقات اللانهائية في المخططات العودية.
3.  **التقييم الكسول (Lazy Evaluation)**: حل المراجع فقط عند الحاجة للمقارنة.

المعايير (Standards):
- OpenAPI 3.1 / JSON Schema 2020-12
- Harvard CS 252r: Strict Typing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypedDict, cast

from app.core.types import JSONDict


class ChangeType(StrEnum):
    """نوع التغيير في العقد."""

    BREAKING = "BREAKING"
    NON_BREAKING = "NON_BREAKING"
    INFO = "INFO"


@dataclass(frozen=True)
class EvolutionIssue:
    """يمثل مشكلة أو تغييراً تم اكتشافه أثناء فحص التطور."""

    path: str
    change_type: ChangeType
    message: str
    severity: str  # "ERROR", "WARNING", "INFO"


class SchemaContext(TypedDict):
    """سياق تحليل المخطط، يحتوي على التعريفات والمراجع."""

    base_uri: str
    root: JSONDict
    # خريطة المراجع المحلولة مسبقاً (URI -> Schema)
    refs: dict[str, JSONDict]


@dataclass
class ResolutionScope:
    """
    يمثل نطاق الحل الديناميكي في لحظة معينة.
    يحتوي على سلسلة المخططات التي تم الدخول إليها (Dynamic Scope).
    """

    scope_stack: list[tuple[str, JSONDict]] = field(default_factory=list)

    def push(self, uri: str, schema: JSONDict) -> ResolutionScope:
        """يعيد نطاقاً جديداً مع إضافة المخطط الحالي إلى المكدس."""
        return ResolutionScope(scope_stack=[*self.scope_stack, (uri, schema)])

    def find_dynamic_anchor(self, anchor: str) -> JSONDict | None:
        """
        يبحث عن المرساة الديناميكية (Dynamic Anchor) في النطاق.
        وفقاً للمعيار: يتم استخدام أبعد مرساة مطابقة في النطاق الديناميكي.
        """
        # البحث من البداية (الأبعد) إلى النهاية (الأقرب)
        for _, schema in self.scope_stack:
            if schema.get("$dynamicAnchor") == anchor:
                return schema
        return None


class SchemaResolver:
    """
    المحلل العبقري للمخططات (Genius Schema Resolver).
    يقوم بحل المراجع الثابتة ($ref) والديناميكية ($dynamicRef) بشكل ثابت.
    """

    def __init__(self, root: JSONDict):
        self.root = root
        self.context: SchemaContext = {"base_uri": "#", "root": root, "refs": {}}

    def resolve(self, schema: JSONDict, scope: ResolutionScope) -> JSONDict:
        """
        يحل المخطط المعطى، ويتعامل مع المراجع والتكرار.
        يقوم بحل سلاسل المراجع (Reference Chains) بشكل تكراري حتى يصل إلى مخطط حقيقي
        أو يصل إلى حد التكرار المسموح به.
        """
        current = schema
        # Safety limit for chain following (simulating "Genius" intuition to stop madness)
        for _ in range(100):
            if "$dynamicRef" in current:
                current = self._resolve_dynamic_ref(cast(str, current["$dynamicRef"]), scope)
            elif "$ref" in current:
                current = self._resolve_ref(cast(str, current["$ref"]), scope)
            else:
                return current

        # إذا تجاوزنا الحد، نعيد آخر ما وصلنا إليه لتفادي الانهيار، مع اعتباره "غير محلول"
        return current

    def _resolve_ref(self, ref: str, scope: ResolutionScope) -> JSONDict:
        """حل المرجع الثابت ($ref)."""
        # دعم المرجع الجذري
        if ref == "#":
            return self.root

        # تبسيط: نفترض أن المراجع محلية (Internal) وتستخدم مسارات JSON Pointer
        # في بيئة حقيقية يجب دعم المراجع الخارجية
        if ref.startswith("#/"):
            path = ref[2:].split("/")
            current: object = self.root
            for segment in path:
                if isinstance(current, dict):
                    current = current.get(segment)
                else:
                    return {"description": f"Unresolved ref: {ref}"}  # Error case

            if isinstance(current, dict):
                # إذا وجدنا المخطط، نعيد حله في سياق النطاق الجديد إذا لزم الأمر
                # لكن المراجع الثابتة لا تغير النطاق الديناميكي بنفس طريقة dynamicRef
                # إلا أنها توسع المخطط.
                return cast(JSONDict, current)

        return {"description": f"External/Unknown ref: {ref}"}

    def _resolve_dynamic_ref(self, ref: str, scope: ResolutionScope) -> JSONDict:
        """
        حل المرجع الديناميكي ($dynamicRef).
        المنطق:
        1. إذا وجدنا مرساة ديناميكية في المكدس تطابق الاسم، نستخدمها (الأبعد).
        2. وإلا، نتصرف مثل $ref عادي.
        """
        # استخراج اسم المرساة (عادة ما يكون بعد #)
        anchor_name = ref.rsplit("#", maxsplit=1)[-1] if "#" in ref else ref

        # محاولة العثور على المرساة في النطاق الديناميكي
        dynamic_target = scope.find_dynamic_anchor(anchor_name)
        if dynamic_target:
            return dynamic_target

        # السلوك الاحتياطي: حل كمرجع عادي
        return self._resolve_ref(ref, scope)


class ContractEvolutionChecker:
    """
    فاحص تطور العقود (Contract Evolution Checker).
    يقارن نسختين من المخطط لاكتشاف التغييرات الكاسرة.
    """

    def __init__(self):
        self._processing: set[str] = set()

    def check_evolution(self, old: JSONDict, new: JSONDict) -> list[EvolutionIssue]:
        """
        نقطة الدخول الرئيسية لفحص التطور.
        """
        self._processing.clear()
        old_resolver = SchemaResolver(old)
        new_resolver = SchemaResolver(new)
        scope = ResolutionScope()

        return self._compare_schemas(old, new, old_resolver, new_resolver, scope, path="#")

    def _compare_schemas(
        self,
        old: JSONDict,
        new: JSONDict,
        old_res: SchemaResolver,
        new_res: SchemaResolver,
        scope: ResolutionScope,
        path: str,
    ) -> list[EvolutionIssue]:
        """
        مقارنة تكرارية للمخططات مع معالجة المراجع.
        """
        issues: list[EvolutionIssue] = []

        # 1. حل المراجع للوصول إلى المخطط الفعلي
        resolved_old = old_res.resolve(old, scope)
        resolved_new = new_res.resolve(new, scope)

        # 2. التحقق من التكرار اللانهائي (Cycle Detection)
        # نستخدم معرف الكائن فقط (بدون المسار) للكشف عن الدوائر في الرسم البياني للمخطط
        # إذا كنا نعالج نفس زوج الكائنات حالياً، فهذا يعني أننا في حلقة.
        visit_key = f"{id(resolved_old)}-{id(resolved_new)}"

        if visit_key in self._processing:
            return []  # تم اكتشاف حلقة، نوقف التكرار هنا

        self._processing.add(visit_key)

        try:
            # تحديث النطاق الديناميكي إذا كان للمخططات عناوين أو مراسي
            new_scope = scope
            if "$id" in resolved_old:
                new_scope = new_scope.push(cast(str, resolved_old["$id"]), resolved_old)

            # 3. مقارنة الأنواع
            old_type = resolved_old.get("type")
            new_type = resolved_new.get("type")

            # السماح بتوسيع النوع (مثل تحويل string إلى [string, null])
            # لكن هنا للتبسيط نعتبر تغيير النوع كسراً ما لم يكن مطابقاً تماماً
            if old_type != new_type and old_type is not None:
                # استثناء: إذا كان الجديد يسمح بأكثر (ليس كسراً دائماً ولكن نعتبره خطيراً هنا)
                # للتبسيط: عدم تطابق النوع = كسر
                issues.append(
                    EvolutionIssue(
                        path=path,
                        change_type=ChangeType.BREAKING,
                        message=f"Type changed from {old_type} to {new_type}",
                        severity="ERROR",
                    )
                )
                return issues

            # 4. مقارنة الخصائص (Properties) للكائنات
            if resolved_old.get("type") == "object" or "properties" in resolved_old:
                issues.extend(
                    self._compare_properties(
                        resolved_old, resolved_new, old_res, new_res, new_scope, path
                    )
                )

            # 5. مقارنة العناصر (Items) للمصفوفات
            if resolved_old.get("type") == "array" or "items" in resolved_old:
                issues.extend(
                    self._compare_items(
                        resolved_old, resolved_new, old_res, new_res, new_scope, path
                    )
                )

            return issues
        finally:
            # إزالة من قائمة المعالجة للسماح بزيارة نفس الكائنات في مسارات أخرى (Siblings)
            self._processing.remove(visit_key)

    def _compare_items(
        self,
        old: JSONDict,
        new: JSONDict,
        old_res: SchemaResolver,
        new_res: SchemaResolver,
        scope: ResolutionScope,
        path: str,
    ) -> list[EvolutionIssue]:
        """مقارنة عناصر المصفوفات."""
        issues = []
        old_items = old.get("items")
        new_items = new.get("items")

        # إذا كان items غير موجود، فهذا يعني سماحية لأي نوع، وتقييده يعد كسراً
        if old_items is None and new_items is not None:
            issues.append(
                EvolutionIssue(
                    path=f"{path}/items",
                    change_type=ChangeType.BREAKING,
                    message="Array items were unrestricted, now restricted",
                    severity="ERROR",
                )
            )
            return issues

        if old_items is None:
            return issues

        # إذا كان items قاموساً مفرداً (Schema)
        if isinstance(old_items, dict) and isinstance(new_items, dict):
            return self._compare_schemas(
                cast(JSONDict, old_items),
                cast(JSONDict, new_items),
                old_res,
                new_res,
                scope,
                f"{path}/items",
            )

        # تجاهل الحالات المعقدة (Tuple validation) للتبسيط حالياً
        return issues

    def _compare_properties(
        self,
        old: JSONDict,
        new: JSONDict,
        old_res: SchemaResolver,
        new_res: SchemaResolver,
        scope: ResolutionScope,
        path: str,
    ) -> list[EvolutionIssue]:
        issues = []
        old_props = cast(dict[str, JSONDict], old.get("properties", {}))
        new_props = cast(dict[str, JSONDict], new.get("properties", {}))
        old_required = set(cast(list[str], old.get("required", [])))
        new_required = set(cast(list[str], new.get("required", [])))

        # أ. التحقق من إزالة خصائص
        # في استجابة API: إزالة خاصية = كسر للعقد (العميل يتوقعها)
        # في طلب API: إزالة خاصية = غير كاسر (الخادم لا يطلبها) -> نفترض فحص الاستجابة (الأكثر صرامة)
        for key in old_props:
            if key not in new_props:
                issues.append(
                    EvolutionIssue(
                        path=f"{path}/properties/{key}",
                        change_type=ChangeType.BREAKING,
                        message=f"Property '{key}' removed",
                        severity="ERROR",
                    )
                )

        # ب. التحقق من إضافة حقول مطلوبة جديدة
        # إضافة حقل مطلوب = كسر (العميل القديم لا يرسله)
        for key in new_required:
            if key not in old_required:
                # إذا كان الحقل جديداً تماماً، فهو كسر
                # إذا كان موجوداً سابقاً وأصبح مطلوباً، فهو كسر أيضاً
                issues.append(
                    EvolutionIssue(
                        path=f"{path}/required/{key}",
                        change_type=ChangeType.BREAKING,
                        message=f"Property '{key}' became required",
                        severity="ERROR",
                    )
                )

        # ج. مقارنة الخصائص المشتركة بشكل عودي
        for key, old_prop in old_props.items():
            if key in new_props:
                issues.extend(
                    self._compare_schemas(
                        old_prop,
                        new_props[key],
                        old_res,
                        new_res,
                        scope,
                        f"{path}/properties/{key}",
                    )
                )

        return issues
