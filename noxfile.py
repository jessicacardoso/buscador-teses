import nox

py_versions = [
    "3.12",
    "3.11",
    "3.10",
]


@nox.session(python=py_versions, venv_backend="uv")
def test_unit(session: nox.Session):
    session.install("pytest")
    session.install("-e", ".[unit]")
    session.run("pytest", "-s", "tests/unit")
