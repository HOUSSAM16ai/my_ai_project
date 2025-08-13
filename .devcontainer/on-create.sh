#!/bin/bash
set -e
echo "
✅ On-Create: Bootstrapping foundational layers...
"
# تثبيت الاعتماديات اللازمة لعمل VS Code بشكل صحيح
pip install -r requirements.txt