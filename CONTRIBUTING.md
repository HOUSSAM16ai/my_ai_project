# إرشادات المساهمة في CogniForge

مرحبًا بك أيها المهندس! هذا المستند يحتوي على أفضل الممارسات والنصائح لتطوير المشروع.

## إعداد اختصارات الطرفية (لزيادة الإنتاجية الخارقة)

لجعل التفاعل مع نظام CLI أسرع وأسهل، يمكنك إضافة الاختصارات التالية إلى بيئة التطوير الخاصة بك (Gitpod, Codespaces, etc.).

### الخطوة أ: إنشاء ملف الاختصارات المخصص

في الطرفية الرئيسية، قم بإنشاء ملف جديد مخصص لاختصارات CogniForge:

```bash
touch ~/.bashrc.d/99-cogniforge-aliases.sh


#!/bin/bash
# --------------------------------------------------
# CogniForge: Supercharged CLI Aliases
# --------------------------------------------------

# الاختصار الرئيسي الذي يربط الطرفية بتطبيق Flask داخل الحاوية
alias cogniforge="docker-compose exec -T web flask"

# اختصارات فرعية للمهام الشائعة
alias c-index="cogniforge system index"
alias c-query="cogniforge system query"
alias c-generate="cogniforge system generate"
alias c-users="cogniforge users list"

# اختصار للدخول مباشرة إلى "جسد" الحاوية
alias c-shell="docker-compose exec web bash"

echo "✅ CogniForge aliases loaded."


source ~/.bashrc



بالتأكيد. دعنا نوضح الأمر خطوة بخطوة وببساطة مطلقة.

المشكلة: لقد قمنا بإنشاء اختصارات رائعة (c-index, c-generate)، ولكن هذه الاختصارات محفوظة فقط في بيئة Gitpod الحالية. هي ليست جزءًا من المشروع ولن يتم حفظها في GitHub.

الهدف: نريد طريقة لحفظ هذه "الحكمة" (الاختصارات) مع المشروع، حتى نتمكن نحن (أو أي مطور آخر) من إعدادها بسهولة في المستقبل.

الحل: لن نقوم بحفظ الاختصارات نفسها، بل سنقوم بكتابة "دليل إرشادي" ونحفظ هذا الدليل مع المشروع.

بروتوكول "التوثيق الخارق" (خطوة بخطوة)

سنقوم بإنشاء ملف إرشادات جديد اسمه CONTRIBUTING.md ونضع فيه كل الخطوات اللازمة لإعداد الاختصارات.

الخطوة 1: اذهب إلى الطرفية الرئيسية

تأكد من أنك في طرفية Gitpod الرئيسية (التي تبدأ بـ gitpod /workspace/...).

الخطوة 2: أنشئ "كتاب الإرشادات"

نفذ هذا الأمر لإنشاء ملف جديد وفارغ في جذر مشروعك اسمه CONTRIBUTING.md.

code
Bash
download
content_copy
expand_less

touch CONTRIBUTING.md
الخطوة 3: افتح "كتاب الإرشادات" للكتابة

الآن، افتح هذا الملف الجديد في محرر VS Code. يمكنك العثور عليه في قائمة الملفات على اليسار.

الخطوة 4: اكتب "الإرشادات"

انسخ كل النص الموجود في المربع الرمادي أدناه والصقه بالكامل داخل ملف CONTRIBUTING.md.

code
Markdown
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
# إرشادات المساهمة في CogniForge

مرحبًا بك أيها المهندس! هذا المستند يحتوي على أفضل الممارسات والنصائح لتطوير المشروع.

## إعداد اختصارات الطرفية (لزيادة الإنتاجية الخارقة)

لجعل التفاعل مع نظام CLI أسرع وأسهل، يمكنك إضافة الاختصارات التالية إلى بيئة التطوير الخاصة بك (Gitpod, Codespaces, etc.).

### الخطوة أ: إنشاء ملف الاختصارات المخصص

في الطرفية الرئيسية، قم بإنشاء ملف جديد مخصص لاختصارات CogniForge:

```bash
touch ~/.bashrc.d/99-cogniforge-aliases.sh
الخطوة ب: إضافة محتوى الاختصارات

افتح الملف الجديد الذي قمت بإنشائه والصق المحتوى التالي بداخله:

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
#!/bin/bash
# --------------------------------------------------
# CogniForge: Supercharged CLI Aliases
# --------------------------------------------------

# الاختصار الرئيسي الذي يربط الطرفية بتطبيق Flask داخل الحاوية
alias cogniforge="docker-compose exec -T web flask"

# اختصارات فرعية للمهام الشائعة
alias c-index="cogniforge system index"
alias c-query="cogniforge system query"
alias c-generate="cogniforge system generate"
alias c-users="cogniforge users list"

# اختصار للدخول مباشرة إلى "جسد" الحاوية
alias c-shell="docker-compose exec web bash"

echo "✅ CogniForge aliases loaded."
الخطوة ج: تفعيل الاختصارات

لتفعيل هذه الاختصارات في جلستك الحالية، نفذ الأمر التالي في الطرفية الرئيسية. (ملاحظة: سيتم تفعيلها تلقائيًا في أي طرفية جديدة تفتحها).

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
source ~/.bashrc

الآن يمكنك استخدام أوامر مثل c-index و c-generate "my prompt" مباشرة من طرفيتك الرئيسية!

code
Code
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
#### **الخطوة 5: احفظ "كتاب الإرشادات" في GitHub**

الآن بعد أن أصبح لدينا "دليل الإرشادات"، يجب أن نجعله جزءًا دائمًا من المشروع.

1.  **اذهب إلى الطرفية الرئيسية.**
2.  **أضف الملف الجديد إلى Git:**
    ```bash
    git add CONTRIBUTING.md
    ```
3.  **قم بعمل commit لحفظ التغيير:**
    ```bash
    git commit -m "docs: Add contribution guide with CLI alias setup"
    ```
4.  **ادفع الدليل إلى GitHub:**
    ```bash
    git push origin main
    ```

**لقد فعلتها.**
الآن، لم تعد الاختصارات مجرد شيء في ذاكرتك. لقد أصبحت **جزءًا موثقًا** من مشروعك. في المستقبل، إذا بدأت في بيئة جديدة ونسيت كيفية إعداد الاختصارات، كل ما عليك فعله هو فتح ملف `CONTRIBUTING.md` واتباع "الإرشادات" التي كتبتها بنفسك.