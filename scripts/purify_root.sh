#!/bin/bash
# Root Purification Script - Surgical Cleanup
# Implements "البساطة الخارقة" (Superhuman Simplicity)

set -e

echo "🎯 Starting Root Purification..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create archive structure
echo "📁 Creating archive structure..."
mkdir -p docs/archive/{fixes,guides,summaries,reports,implementations,troubleshooting}

# Count before cleanup
total_md=$(ls -1 *.md 2>/dev/null | wc -l)
echo "📊 Found $total_md markdown files in root"

# Keep only essential documentation in root
KEEP_FILES=(
    "README.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
    "LICENSE.md"
    "SIMPLICITY_PRINCIPLES_GUIDE_AR.md"
    "SIMPLICITY_PRINCIPLES_GUIDE_EN.md"
    "SIMPLICITY_QUICK_REFERENCE.md"
    "SIMPLICITY_VALIDATION_REPORT.md"
    "SUPERHUMAN_SIMPLICITY_ARCHITECTURE.md"
    "SUPERHUMAN_SIMPLICITY_FRAMEWORK.md"
)

echo ""
echo "✅ Files to KEEP in root:"
for file in "${KEEP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   • $file"
    fi
done

echo ""
echo "📦 Moving files to archive..."

# Move FIX_* files
echo "   Moving FIX_* files..."
if compgen -G "FIX_*.md" > /dev/null; then
    mv FIX_*.md docs/archive/fixes/ 2>/dev/null || echo "   Warning: Some FIX_*.md files could not be moved"
fi
if compgen -G "*_FIX*.md" > /dev/null; then
    mv *_FIX*.md docs/archive/fixes/ 2>/dev/null || echo "   Warning: Some *_FIX*.md files could not be moved"
fi

# Move GUIDE files
echo "   Moving *_GUIDE*.md files..."
if compgen -G "*_GUIDE*.md" > /dev/null; then
    mv *_GUIDE*.md docs/archive/guides/ 2>/dev/null || echo "   Warning: Some GUIDE files could not be moved"
fi
mv *_QUICK_REF*.md docs/archive/guides/ 2>/dev/null || true
mv *_QUICKSTART*.md docs/archive/guides/ 2>/dev/null || true

# Move SUMMARY files
echo "   Moving *_SUMMARY*.md files..."
mv *_SUMMARY*.md docs/archive/summaries/ 2>/dev/null || true

# Move REPORT files
echo "   Moving *_REPORT*.md files..."
mv *_REPORT*.md docs/archive/reports/ 2>/dev/null || true

# Move IMPLEMENTATION files
echo "   Moving *_IMPLEMENTATION*.md files..."
mv *_IMPLEMENTATION*.md docs/archive/implementations/ 2>/dev/null || true

# Move TROUBLESHOOTING/VERIFICATION files
echo "   Moving troubleshooting files..."
mv *_TROUBLESHOOTING*.md docs/archive/troubleshooting/ 2>/dev/null || true
mv *_VERIFICATION*.md docs/archive/troubleshooting/ 2>/dev/null || true
mv *_STATUS*.md docs/archive/troubleshooting/ 2>/dev/null || true

# Move Arabic documentation
echo "   Moving Arabic documentation..."
mv الحل*.md docs/archive/fixes/ 2>/dev/null || true

# Move remaining non-essential MD files (except KEEP_FILES)
echo "   Moving remaining non-essential files..."
for md_file in *.md; do
    # Skip if file doesn't exist
    [ -f "$md_file" ] || continue

    # Check if file is in KEEP_FILES
    keep=false
    for keep_file in "${KEEP_FILES[@]}"; do
        if [ "$md_file" = "$keep_file" ]; then
            keep=true
            break
        fi
    done

    # Move if not in keep list
    if [ "$keep" = false ]; then
        mv "$md_file" docs/archive/guides/ 2>/dev/null || true
    fi
done

# Count after cleanup
remaining_md=$(ls -1 *.md 2>/dev/null | wc -l)
archived=$((total_md - remaining_md))

echo ""
echo "✅ Root Purification Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Statistics:"
echo "   • Total files processed: $total_md"
echo "   • Files archived: $archived"
echo "   • Files kept in root: $remaining_md"
echo ""
echo "📁 Root now contains only:"
ls -1 *.md 2>/dev/null | sed 's/^/   • /'
echo ""
echo "🎯 Next steps:"
echo "   1. Review docs/archive/ structure"
echo "   2. Run: make clean  # to remove temporary files"
echo "   3. Run: git status  # to see changes"
echo ""
echo "💡 Philosophy: \"احذف، ادمج، ثم ابنِ\" - Delete, Merge, then Build"
