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

EXTENSION_TITLE = 'More Source Control Buttons'
EXTENSION_ID = 'more-scm-buttons'

CONFIG_GROUP_TITLE = 'Button Visibility'
CONFIG_PREFIX = 'moreSourceControlButtons'


def enable_ansi_support() -> None:
	'''Enable ANSI escape sequence support on Windows terminals.'''

	if os.name != 'nt':
		return

	kernel32 = ctypes.windll.kernel32

	kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def print_traceback() -> None:
	'''Print formatted traceback.'''

	sys.excepthook(*sys.exc_info())


def parse_buttons(buttons: dict[str, dict], include: Iterable[str] | Literal['*'] = '*') -> Iterable[tuple[tuple[str, dict], dict, dict]]:
	'''Returns: `((configuration_data_key, configuration_data_value), commands_data, menus_data)`'''

	index = 1
	n_missing = 0
	n_errors = 0
	for id in buttons if include == '*' else include:
		try:
			if not id:
				continue

			if id not in buttons:
				print(f'-- \x1b[90m{id}\x1b[0m')
				n_missing += 1
				continue

			data = buttons[id]

			more = '' if data['more'] is None else str(data['more'])
			command_id = '' if data['command_id'] is None else str(data['command_id'])
			command_name = '' if data['command_name'] is None else str(data['command_name'])
			icon = '' if data['icon'] is None else str(data['icon'])
			when = '' if data['when'] is None else str(data['when'])

			default = data['default']
			if not isinstance(default, bool):
				raise TypeError('default must be a bool')

			config_name = f'{CONFIG_PREFIX}.enable{id}'
			config_condition = f'config.{config_name}'
			full_command = f'{EXTENSION_ID}.{command_id}'

			out_description = f'Show button for command `{command_name}`.'
			if more:
				out_description += f' *{more}*'

			out_when = ' && '.join([
				f'(config.{CONFIG_PREFIX}.enableAll || {config_condition})',
				*(when and [when])
			])

			config_data = {
				'markdownDescription': out_description,
				'type': 'boolean',
				'default': default,
				'order': index,
			}

			out_configuration_data = (config_name, config_data)

			out_commands_data = {
				'category': EXTENSION_TITLE,
				'title': command_name,
				'command': full_command,
				'icon': f'$({icon})',
			}

			out_menus_data = {
				'command': full_command,
				'when': out_when,
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
		if group.get('title') == CONFIG_GROUP_TITLE
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
