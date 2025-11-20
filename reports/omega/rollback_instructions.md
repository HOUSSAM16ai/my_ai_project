# Rollback Instructions

**WARNING**: Rolling back will revert the architecture to the legacy Flask state. This is not recommended unless critical production failure occurs.

## Procedure

1. **Checkout Previous Branch**
   Identify the commit SHA before the `omega/obliterate` merge.
   ```bash
   git checkout <PREVIOUS_SHA>
   ```
   Or if you used a branch:
   ```bash
   git checkout main
   ```

2. **Restore Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Clean Artifacts**
   Remove any generated reports or temporary files:
   ```bash
   rm -rf reports/omega
   ```

4. **Verify Legacy State**
   Run the old test suite (if available) to ensure Flask app boots.
   ```bash
   python -m pytest
   ```

## Caveats
- Database migrations created during Omega phase might need manual downgrade if they altered schema significantly (though we aimed for compatibility).
- New environment variables (Pydantic settings) might be missing from the old `.env` parser if not backward compatible.
