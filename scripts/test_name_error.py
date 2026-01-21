
def test_func():
    global Bot
    # If Bot is not in globals, accessing it here should raise NameError IF we didn't check globals() first
    # But we do check globals() first.
    # However, let's see if the order matters or if there's some other issue.
    
    print(f"Globals has Bot: {'Bot' in globals()}")
    
    try:
        if "Bot" not in globals() or Bot is None:
            print("Bot missing or None")
            Bot = "Fixed"
    except NameError as e:
        print(f"Caught NameError: {e}")
    except Exception as e:
        print(f"Caught {type(e).__name__}: {e}")

print("--- Test 1: Bot not in globals ---")
if "Bot" in globals():
    del Bot
test_func()

print("\n--- Test 2: Bot in globals ---")
Bot = "Original"
test_func()
print(f"Bot after func: {Bot}")
