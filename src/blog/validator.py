def validate_width_and_height(cls, value, values, type):
    assert (
        value >= 32 and value <= 1024 and value % 8 == 0
    ), f"{type} must be between 32 and 1024 and divisible by 8"
    return value
