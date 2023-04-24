try:
    raise AssertionError("custom message")
except Exception as E:
    print(E, str(E))