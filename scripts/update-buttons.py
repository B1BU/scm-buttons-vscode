import ctypes
import json
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import yaml

ROOT_DIR = Path('..')
PACKAGE_FILE = ROOT_DIR / 'package.json'

DATA_DIR = Path('data')
BUTTONS_FILE = DATA_DIR / 'buttons.yml'
INCLUDE_FILE = DATA_DIR / 'include.txt'

BUTTON_VISIBILITY_CONFIG_GROUP_TITLE = 'Button Visibility'


def enable_ansi_support() -> None:
	'''Enable ANSI escape sequence support on Windows terminals.'''

	if os.name != 'nt':
		return

	kernel32 = ctypes.windll.kernel32

	kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def print_traceback() -> None:
	'''Print formatted traceback.'''

	sys.excepthook(*sys.exc_info())


def parse_buttons(buttons: dict, include: Iterable | Literal['*'] = '*') -> Iterable[tuple[tuple[str, dict], dict, dict]]:
	'''Returns: `((configuration_data_key, configuration_data_value), commands_data, menus_data)`'''

	if include == '*':
		include = buttons.keys()

	n_missing = 0
	n_errors = 0

	index = 1
	for id in include:
		try:
			if id not in buttons:
				print(f'-- \x1b[90m{id}\x1b[0m')
				n_missing += 1
				continue

			data = buttons[id]

			title = data['title']
			command = data['command']
			icon = data['icon']
			when = data['when']
			default = data['default']

			config_name = f'scm-buttons.show{id}'
			ext_command = f'scm-buttons.{command}'
			config_condition = f'config.{config_name}'

			config_data = {
				'type': 'boolean',
				'default': default,
				'markdownDescription': f'Show button for command `{command}`.',
			}

			out_configuration_data = (config_name, config_data)

			out_commands_data = {
				'category': 'Source Control Buttons',
				'command': ext_command,
				'title': title,
				'icon': f'$({icon})',
			}

			out_menus_data = {
				'when': f'config.scm-buttons.showAll && {when} || {config_condition} && {when}' if when else config_condition,
				'command': ext_command,
				'group': f'navigation@{index}',
			}

			print(f'{index:>2} \x1b[92m{id}\x1b[0m')

			index += 1

			yield out_configuration_data, out_commands_data, out_menus_data

		except Exception:
			n_errors += 1
			print(f'-- \x1b[91m{id}\x1b[0m')
			print_traceback()

	# Compile warnings
	warnings = []

	if n_missing > 0:
		warnings.append(f"\x1b[93m{n_missing} MISSING\x1b[0m")

	if n_errors > 0:
		warnings.append(f'\x1b[91m{n_errors} ERRORS\x1b[0m')

	if warnings:
		print(' | '.join(warnings))


def update_package() -> None:
	package_data = json.load(PACKAGE_FILE.open())

	config_group_index = next(
		i for i, group in enumerate(package_data['contributes']['configuration'])
		if group.get('title') == BUTTON_VISIBILITY_CONFIG_GROUP_TITLE
	)

	include = INCLUDE_FILE.read_text().splitlines()
	buttons = yaml.safe_load(BUTTONS_FILE.open('r'))

	configuration_data = {}
	commands_data = []
	menus_data = []

	for this_configuration_data, this_commands_data, this_menus_data in parse_buttons(buttons, include):
		configuration_data.update([this_configuration_data])
		commands_data.append(this_commands_data)
		menus_data.append(this_menus_data)

	package_data['contributes']['configuration'][config_group_index]['properties'] = configuration_data
	package_data['contributes']['commands'] = commands_data
	package_data['contributes']['menus']['scm/title'] = menus_data

	json.dump(package_data, PACKAGE_FILE.open('w', encoding='utf-8'), indent=4)


def main() -> None:
	enable_ansi_support()
	update_package()


if __name__ == "__main__":
	main()
