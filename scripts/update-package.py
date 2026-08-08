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
NAMESPACE = 'moreSourceControlButtons'
CONFIG_CATEGORY_PREFIX = 'buttonVisibility'


def enable_ansi_support() -> None:
	'''Enable ANSI escape sequence support on Windows terminals.'''

	if os.name != 'nt':
		return

	kernel32 = ctypes.windll.kernel32

	kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def parse_buttons(buttons: dict[str, dict], include: Iterable[str] | Literal['*'] = '*') -> Iterable[tuple[str, tuple[str, dict], dict, list[str], dict]]:
	'''Returns: `(configuration_category, (configuration_data_key, configuration_data_value), commands_data, menus_list, menus_data)`'''

	index = 1
	missing = []
	failed = []
	for id in buttons if include == '*' else include:
		try:
			if not id:
				continue

			if id not in buttons:
				missing.append(id)
				print(f'-- \x1b[90m{id}\x1b[0m')
				continue

			data = buttons[id]

			category = '' if data['category'] is None else str(data['category'])
			name = data['name']
			info = '' if data['info'] is None else str(data['info'])
			icon = data['icon']
			command = data['command']
			when = '' if data['when'] is None else str(data['when'])
			default = False if data['default'] is None else data['default']
			menus = [] if data['menus'] is None else data['menus']

			if not name:
				raise ValueError('button name not defined')

			if not icon:
				raise ValueError('button icon not defined')

			if not command:
				raise ValueError('button command not defined')

			if not isinstance(default, bool):
				raise TypeError('default must be a bool')

			if not menus:
				raise ValueError('button menus not defined')

			config_name = f'{NAMESPACE}.enable{id}'

			full_command = f'{NAMESPACE}.{command}'

			description = f'Show button for command `{name}`.'
			if info:
				description += f' *{info}*'

			full_when = f'(config.{NAMESPACE}.enableAll || config.{config_name})'
			if when:
				full_when += f' && {when}'

			full_category = f'{CONFIG_CATEGORY_PREFIX}{category}'

			config_data = {
				'markdownDescription': description,
				'type': 'boolean',
				'default': default,
				'order': index,
			}

			configuration_data = (config_name, config_data)

			commands_data = {
				'category': EXTENSION_TITLE,
				'title': name,
				'command': full_command,
				'icon': f'$({icon})',
				'generated': True,
			}

			menus_data = {
				'command': full_command,
				'when': full_when,
				'group': f'navigation@{index}',
				'generated': True,
			}

			print(f'{index:>2} \x1b[92m{id}\x1b[0m')

			index += 1

			yield full_category, configuration_data, commands_data, menus, menus_data

		except Exception:
			print(f'-- \x1b[91m{id}\x1b[0m')
			failed.append(id)
			sys.excepthook(*sys.exc_info())

	if missing or failed:
		lines = []

		if missing:
			lines.extend([f'\x1b[93mMISSING {len(missing)}\x1b[0m', *(f'- \x1b[33m{id}\x1b[0m' for id in missing)])

		if failed:
			lines.extend([f'\x1b[91mFAILED {len(failed)}\x1b[0m', *(f'- \x1b[31m{id}\x1b[0m' for id in failed)])

		text = '\n'.join(lines)

		print(f'\n{text}\n')


def update_package() -> None:
	include = INCLUDE_FILE.read_text().splitlines()

	with BUTTONS_FILE.open() as file:
		buttons_data: dict = yaml.safe_load(file)

	with PACKAGE_FILE.open() as file:
		package_data: dict = yaml.safe_load(file)

	contributes: dict = package_data['contributes']

	configuration: list = contributes['configuration']

	for category in configuration:
		category_id = category.get('id')

		if category_id and category_id.startswith(CONFIG_CATEGORY_PREFIX):
			category['properties'] = {}

	commands: list = contributes['commands']

	commands[:] = [
		command
		for command in commands
		if not command.get('generated')
	]

	menus = contributes['menus']

	for menu, buttons in list(menus.items()):
		menus[menu] = [
			button
			for button in buttons
			if not button.get('generated')
		]

		if not menus[menu]:
			del menus[menu]

	categories = {
		category.get('id'): category
		for category in configuration
	}

	for configuration_category, configuration_data, commands_data, menus_list, menus_data in parse_buttons(buttons_data, include):
		categories[configuration_category]['properties'].update([configuration_data])
		commands.append(commands_data)
		for menu in menus_list:
			menus.setdefault(menu, []).append(menus_data)

	with PACKAGE_FILE.open('w', encoding='utf-8') as file:
		json.dump(package_data, file, indent=4)


def main() -> None:
	enable_ansi_support()
	update_package()


if __name__ == "__main__":
	main()
