
def test_func():
    global Bot
    # Simulate Bot not being in globals
    if "Bot" not in globals() or Bot is None:
        print("Bot not found, importing...")
        Bot = "ImportedBot"
    else:
        print(f"Bot found: {Bot}")

print("Test 1: Bot not defined")
try:
    test_func()
except NameError as e:
    print(f"Caught expected error: {e}")
except Exception as e:
    print(f"Caught unexpected error: {e}")

print("\nTest 2: Bot defined")
Bot = "ExistingBot"
test_func()
