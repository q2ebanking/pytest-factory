import os
from pathlib import Path

pytest_plugins = ["pytest_factory.framework.pytest"]


def write_readme_examples_to_file():
    readme_path = Path(__file__).parent.parent.joinpath('README.md')
    in_code_block = False
    files = {}
    file_lines_buffer = []
    with open(readme_path) as readme_f:
        file_name = ''
        for line in readme_f.readlines():
            if '```' in line:
                if in_code_block:
                    in_code_block = False
                    files[file_name] = file_lines_buffer
                    file_lines_buffer = []
                else:
                    in_code_block = True
            elif line[0] in {';', '#'} and in_code_block:
                file_name = line[1:-1]
            elif in_code_block:
                file_lines_buffer.append(line)

    out_dir = Path(__file__).parent.joinpath('test_factory_tests')
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    for file_name, file_lines in files.items():
        if file_name in {'conftest.py', 'config.ini'}:
            continue
        file_path = out_dir.joinpath(file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'w') as new_file:
            new_file.writelines(file_lines)


write_readme_examples_to_file()
