import os
import pathlib
import shutil
from typing import Union

CURRENT_ENGINES = set()


def _get_engines_dir() -> str:
    ENGINES_DIR = "./tmp"
    if not pathlib.Path(ENGINES_DIR).exists():
        os.mkdir(ENGINES_DIR)
    return ENGINES_DIR


def pull_engine(repo: str) -> int:
    engines_dir = _get_engines_dir()
    command = f"cd {engines_dir} && git clone {repo}"
    return os.system(command)


def get_engine_exe(name: str, branch: str, make_dir: str) -> Union[str, None]:
    engines_dir = _get_engines_dir()
    engine_path = pathlib.Path(engines_dir, name)
    print(engine_path)
    if engine_path.exists():
        unique_name = f"{name}-{branch}"
        if unique_name not in CURRENT_ENGINES:
            command = f"cd {engine_path} && git checkout {branch} && cd {make_dir} && make EXE={unique_name}"
            assert os.system(command) == 0
            CURRENT_ENGINES.add(f"{unique_name}")
        return f"{engine_path}/{unique_name}"
    return None


def clear():
    shutil.rmtree(_get_engines_dir())
