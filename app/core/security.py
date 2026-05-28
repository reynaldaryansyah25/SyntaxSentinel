from secrets import compare_digest


def verify_shared_secret(provided_token: str | None, expected_token: str) -> bool:
    if not expected_token or not provided_token:
        return False
    return compare_digest(provided_token, expected_token)
