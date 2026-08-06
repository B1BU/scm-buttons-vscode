import json
import sys
from pathlib import Path

import yaml

ROOT_PATH = Path('..')
PACKAGE_FILE = ROOT_PATH / 'package.json'

OUT_DIR = Path('buttons')
OUT_FILE_DATA = OUT_DIR / 'data.yml'
OUT_FILE_INCLUDE = OUT_DIR / 'include.txt'

ERROR_PREFIX = '\x1b[91m[ERROR]\x1b[0m'


def print_traceback() -> None:
	'''Print formatted traceback.'''

	exc_type, exc_value, exc_tb = sys.exc_info()

	sys.excepthook(exc_type, exc_value, exc_tb)


def get_ids(contributes: dict) -> list[str]:
	ids = []
	for item in contributes['configuration'][0]['properties']:
		key = item.removeprefix('scm-buttons.show')
		ids.append(key)

	return ids


def compile_buttons_data(contributes: dict) -> dict:
	ids = get_ids(contributes)

	out_data = {}
	for id in ids:
		try:
			config_id = f'scm-buttons.show{id}'

			# "configuration"
			data_configuration: dict = contributes['configuration'][0]['properties'][config_id]

			default: bool = data_configuration['default']

			# "menus"
			data_menus: dict = next(item for item in contributes['menus']['scm/title'] if item['when'].endswith(config_id))

			full_command: str = data_menus['command']

			command: str = full_command.removeprefix('scm-buttons.')

			when: str = data_menus['when']

			config_condition = f'config.{config_id}'
			if config_condition in when:
				conditions = when.split(' && ')
				conditions.remove(config_condition)
				when = ' && '.join(conditions)

			# "commands"
			data_commands: dict = next(item for item in contributes['commands'] if item['command'] == full_command)

			title: str = data_commands['title']

			icon: str = data_commands['icon']
			icon = icon.removesuffix(')').removeprefix('$(')

			# Add item
			out_data[id] = {
				'title': title,
				'command': command,
				'icon': icon,
				'when': when,
				'default': default,
			}

			print(f'+ {id}')
		except Exception:  # ruff: ignore[try-except-in-loop]
			print(f'{ERROR_PREFIX} {id}:')
			print_traceback()

	return out_data


def main() -> None:
	package_data = json.load(PACKAGE_FILE.open())

	contributes = package_data['contributes']

	buttons_data = compile_buttons_data(contributes)

	include_text = '\n'.join(buttons_data)

	OUT_DIR.mkdir(parents=True, exist_ok=True)

	yaml.dump(buttons_data, OUT_FILE_DATA.open('w'), sort_keys=False)

	OUT_FILE_INCLUDE.write_text(include_text)


if __name__ == "__main__":
	main()
