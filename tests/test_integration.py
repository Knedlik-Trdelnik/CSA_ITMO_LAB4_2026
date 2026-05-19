import contextlib
import importlib
import io
import os
import re
import sys
from pathlib import Path

import pytest
import yaml

def str_presenter(dumper, data):
    if '\n' in data:
        data = data.replace('\r', '')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter, Dumper=yaml.SafeDumper)

ROOT_DIR = Path(__file__).resolve().parent.parent
TEST_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT_DIR / "examples"
COMPILED_DIR = ROOT_DIR / "compiled"
GOLDEN_DIR = TEST_DIR / "golden"

sys.path.insert(0, str(ROOT_DIR))

GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
COMPILED_DIR.mkdir(parents=True, exist_ok=True)

TEST_FILES = sorted(
    f.name for f in EXAMPLES_DIR.iterdir()
    if f.is_file() and f.suffix == ".txt" and not f.name.endswith("_in.txt")
)


def fresh_modules():
    import translator as translator_module
    import machine as machine_module

    translator_module = importlib.reload(translator_module)
    machine_module = importlib.reload(machine_module)

    return translator_module, machine_module


def normalize_log(text: str) -> list[str]:
    text = re.sub(r"<if-end-\d+>", "<if-end-ID>", text)
    text = re.sub(r"<str-end-\d+>", "<str-end-ID>", text)
    text = re.sub(r"<while-end-\d+>", "<while-end-ID>", text)

    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def run_pipeline(base_name: str) -> str:
    translator, machine = fresh_modules()

    source_no_ext = EXAMPLES_DIR / base_name
    bin_file = COMPILED_DIR / f"{base_name}.bin"
    conf_file = COMPILED_DIR / f"{base_name}_config.json"

    schedule_in = EXAMPLES_DIR / f"{base_name}_in.txt"
    schedule_out = COMPILED_DIR / f"{base_name}_shedule.txt"

    if schedule_in.exists():
        input_text = schedule_in.read_text(encoding="utf-8")
        translator.makeShedule(input_text, filename=str(schedule_out))
    else:
        input_text = ""
        schedule_out.write_text("", encoding="utf-8")

    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        translator.main(source=str(source_no_ext))
        print("\n" + "=" * 40 + "\n")
        machine.run_cpu(str(bin_file), str(schedule_out), str(conf_file))

    return stdout_buffer.getvalue(), input_text


@pytest.mark.parametrize("source_file", TEST_FILES)
def test_golden(source_file):
    source_path = EXAMPLES_DIR / source_file
    base_name = Path(source_file).stem

    source_code = source_path.read_text(encoding="utf-8")
    raw_output, input_text = run_pipeline(base_name)
    actual_output = normalize_log(raw_output)

    test_data = {
        "in_source": source_code,
        "in_stdin": input_text,
        "out_log": actual_output,
    }

    golden_file = GOLDEN_DIR / f"{base_name}.yml"
    update_golden = os.environ.get("UPDATE_GOLDEN") == "1"

    if not golden_file.exists() or update_golden:
        with golden_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                test_data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=120,
            )
        pytest.skip(f"Golden file updated for {source_file}. Run again to test.")

    with golden_file.open("r", encoding="utf-8") as f:
        expected_data = yaml.safe_load(f)

    assert test_data == expected_data, f"Вывод для {source_file} не совпадает с эталоном!"