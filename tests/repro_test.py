import bcrypt


def test_bcrypt_import():
    assert bcrypt.__version__ is not None
