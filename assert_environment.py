# ---------- ENVIRONMENT CHECK ----------
import sys

if sys.version_info.major != 3:
    print("============================================")
    print("CRITICAL ERROR: Python3.x is Required")
    print(sys.version_info)
    print("============================================\n\n")

    raise EnvironmentError("This module requires Python 3!")


# Check if running inside a virtual environment
if not (
    hasattr(sys, "real_prefix")
    or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
):
    raise EnvironmentError("Not running inside a virtual environment!")
