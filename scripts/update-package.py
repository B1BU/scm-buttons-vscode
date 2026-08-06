import json
import sys
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

import yaml

ROOT_PATH = Path('..')
PACKAGE_FILE = ROOT_PATH / 'package.json'

BUTTON_DATA_FILE = Path('buttons/data.yml')
BUTTON_INCLUDE_FILE = Path('buttons/include.txt')

ERROR_PREFIX = '\x1b[91m[ERROR]\x1b[0m'


def print_traceback() -> None:
	'''Print formatted traceback.'''

	exc_type, exc_value, exc_tb = sys.exc_info()

	sys.excepthook(exc_type, exc_value, exc_tb)


def parse_buttons(buttons_data: dict, include: Iterable | None = None) -> Iterable[tuple[tuple[str, dict], dict, dict]]:
	if include is None:
		include = buttons_data.keys()

	i = 1
	for id in include:
		try:
			if id not in buttons_data:
				print(f'{ERROR_PREFIX} {id} not found')
				continue

			data = buttons_data[id]

			title = data['title']
			command = data['command']
			icon = data['icon']
			when = data['when']
			default = data['default']

			config = f'scm-buttons.show{id}'
			ext_command = f'scm-buttons.{command}'
			config_condition = f'config.{config}'

			configuration_data = {
				'type': 'boolean',
				'default': default,
				'markdownDescription': f'Show button for command `{command}`.',
			}

			out_configuration = (config, configuration_data)

			out_commands = {
				'category': 'Source Control Buttons',
				'command': ext_command,
				'title': title,
				'icon': f'$({icon})',
			}

			out_menus = {
				'when': f'config.scm-buttons.showAll && {when} || {config_condition} && {when}' if when else config_condition,
				'command': ext_command,
				'group': f'navigation@{i}',
			}

			i += 1
			print(f'+ {id}')

			yield out_configuration, out_commands, out_menus

		except Exception:
			print(f'{ERROR_PREFIX} {id}:')
			print_traceback()


def main() -> None:
	package_data = json.load(PACKAGE_FILE.open())
	button_include = BUTTON_INCLUDE_FILE.read_text().splitlines()
	button_data = yaml.safe_load(BUTTON_DATA_FILE.open('r'))

	new_package_data = deepcopy(package_data)

	new_package_data['contributes']['configuration'][0]['properties'] = {}
	new_package_data['contributes']['commands'] = []
	new_package_data['contributes']['menus']['scm/title'] = []

	for configuration, commands, menus in parse_buttons(button_data, button_include):
		config, config_value = configuration
		new_package_data['contributes']['configuration'][0]['properties'][config] = config_value
		new_package_data['contributes']['commands'].append(commands)
		new_package_data['contributes']['menus']['scm/title'].append(menus)

	json.dump(new_package_data, PACKAGE_FILE.open('w', encoding='utf-8'), indent=4)


if __name__ == "__main__":
	main()
