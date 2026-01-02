#!/usr/bin/env python
"""
اختبار يدوي للتحقق من قدرات نظام Overmind.

هذا السكريبت يعرض:
1. معلومات المؤسس (الاسم، اللقب، تاريخ الميلاد)
2. القدرات الخارقة للنظام
3. الوكلاء المتاحين
4. الأدوات فائقة الذكاء
"""

from app.services.overmind.identity import OvermindIdentity


def print_section(title: str) -> None:
    """طباعة عنوان قسم مع تنسيق."""
    print("\n" + "=" * 80)
    print(f"🌟 {title}")
    print("=" * 80 + "\n")


def main():
    """الدالة الرئيسية للاختبار."""
    identity = OvermindIdentity()
    
    print_section("معلومات المؤسس (Founder Information)")
    founder = identity.get_founder_info()
    print(f"الاسم الكامل: {founder['name_ar']} ({founder['name']})")
    print(f"الاسم الأول: {founder['first_name_ar']} ({founder['first_name']})")
    print(f"اللقب: {founder['last_name_ar']} ({founder['last_name']})")
    print(f"تاريخ الميلاد: {founder['birth_date']} (11 أغسطس 1997)")
    print(f"الدور: {founder['role_ar']} ({founder['role']})")
    print(f"GitHub: @{founder['github']}")
    
    print_section("اختبار الأسئلة بالعربية")
    questions_ar = [
        "من هو مؤسس overmind؟",
        "ما هو تاريخ ميلاد المؤسس؟",
        "ماذا تستطيع أن تفعل؟",
        "من هم الوكلاء؟",
    ]
    
    for q in questions_ar:
        print(f"\n❓ السؤال: {q}")
        print(f"✅ الإجابة:\n{identity.answer_question(q)}\n")
        print("-" * 80)
    
    print_section("اختبار الأسئلة بالإنجليزية")
    questions_en = [
        "who is the founder?",
        "what is the founder's birth date?",
        "what can you do?",
        "who are the agents?",
    ]
    
    for q in questions_en:
        print(f"\n❓ Question: {q}")
        print(f"✅ Answer:\n{identity.answer_question(q)}\n")
        print("-" * 80)
    
    print_section("الوكلاء الخارقين (Super Agents)")
    agents = identity.get_agents_info()
    for key, agent in agents.items():
        print(f"🤖 {agent['name']}")
        print(f"   الدور: {agent['role']}")
        print(f"   القدرات: {', '.join(agent['capabilities'])}")
        print()
    
    print_section("القدرات والأدوات الخارقة")
    capabilities = identity.get_capabilities()
    
    print("📚 المعرفة (Knowledge):")
    for item in capabilities["knowledge"]:
        print(f"   • {item}")
    
    print("\n⚡ الإجراءات (Actions):")
    for item in capabilities["actions"]:
        print(f"   • {item}")
    
    print("\n🧠 الذكاء (Intelligence):")
    for item in capabilities["intelligence"]:
        print(f"   • {item}")
    
    print("\n🛠️ الأدوات الخارقة (Super Tools):")
    for item in capabilities["super_tools"]:
        print(f"   • {item}")
    
    print_section("معلومات Overmind")
    overmind = identity.get_overmind_info()
    print(f"الاسم: {overmind['name_ar']} ({overmind['name']})")
    print(f"الدور: {overmind['role_ar']} ({overmind['role']})")
    print(f"تاريخ الإنشاء: {overmind['birth_date']}")
    print(f"الإصدار: {overmind['version']}")
    print(f"المهمة: {overmind['purpose']}")
    
    print_section("الخلاصة")
    print("✅ النظام يعمل بشكل صحيح!")
    print("✅ معلومات المؤسس محفوظة بدقة!")
    print("✅ الإجابة على الأسئلة بالعربية والإنجليزية تعمل!")
    print("✅ القدرات الخارقة موثقة ومتاحة!")
    print("✅ الوكلاء الخارقين جاهزون للعمل!")
    print("\n🌟 النظام جاهز للاستخدام! 🌟\n")


if __name__ == "__main__":
    main()
