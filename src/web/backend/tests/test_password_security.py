from argon2 import extract_parameters, Type

from wayfinder.infrastructure.passwords import Argon2PasswordHasher, load_common_passwords


def test_password_hash_is_argon2id_with_owasp_minimum_and_random_salt():
    hasher = Argon2PasswordHasher()
    password = "Một mật khẩu riêng tư 2026"
    first, second = hasher.hash(password), hasher.hash(password)
    parameters = extract_parameters(first)
    assert first.startswith("$argon2id$") and first != second
    assert password not in first
    assert parameters.type is Type.ID
    assert parameters.memory_cost >= 19 * 1024
    assert parameters.time_cost >= 2 and parameters.parallelism >= 1
    assert hasher.verify(first, password)
    assert not hasher.verify(first, "incorrect")


def test_verifier_rejects_malformed_hash_and_dummy_hash_is_real_argon2id():
    hasher = Argon2PasswordHasher()
    assert not hasher.verify("malformed", "password")
    assert hasher.dummy_hash.startswith("$argon2id$")
    assert not hasher.verify(hasher.dummy_hash, "not-the-random-dummy-password")


def test_bundled_common_password_list_is_available_without_network():
    passwords = load_common_passwords()
    assert len(passwords) >= 9900
    assert {"password", "12345678", "123456789", "qwerty"} <= passwords
