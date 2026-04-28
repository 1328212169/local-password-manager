import sys
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

try:
    import crypto
    print("crypto imported successfully")
except Exception as e:
    print(f"Error importing crypto: {e}")

try:
    import password_generator
    print("password_generator imported successfully")
except Exception as e:
    print(f"Error importing password_generator: {e}")

try:
    import batch_importer
    print("batch_importer imported successfully")
except Exception as e:
    print(f"Error importing batch_importer: {e}")

try:
    import settings_dialog
    print("settings_dialog imported successfully")
except Exception as e:
    print(f"Error importing settings_dialog: {e}")

try:
    import txt_converter
    print("txt_converter imported successfully")
except Exception as e:
    print(f"Error importing txt_converter: {e}")

try:
    import floating_window
    print("floating_window imported successfully")
except Exception as e:
    print(f"Error importing floating_window: {e}")

print("Test completed")