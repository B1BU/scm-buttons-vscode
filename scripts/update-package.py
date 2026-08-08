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

CONFIG_PREFIX = 'moreSourceControlButtons'
CONFIG_CATEGORY_PREFIX = 'buttonVisibility'


def enable_ansi_support() -> None:
	'''Enable ANSI escape sequence support on Windows terminals.'''

	if os.name != 'nt':
		return

	kernel32 = ctypes.windll.kernel32

	kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def parse_buttons(buttons: dict[str, dict], include: Iterable[str] | Literal['*'] = '*') -> Iterable[tuple[tuple[str, dict], dict, dict]]:
	'''Returns: `(configuration_category, (configuration_data_key, configuration_data_value), commands_data, menus_data)`'''

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
			name = '' if data['name'] is None else str(data['name'])
			info = '' if data['info'] is None else str(data['info'])
			icon = '' if data['icon'] is None else str(data['icon'])
			command = '' if data['command'] is None else str(data['command'])
			when = '' if data['when'] is None else str(data['when'])
			default = False if data['default'] is None else data['default']

			if not name:
				raise ValueError('button name not defined')

			if not icon:
				raise ValueError('button icon not defined')

			if not command:
				raise ValueError('button cpmmand not defined')

			if not isinstance(default, bool):
				raise TypeError('default must be a bool')

			config_name = f'{CONFIG_PREFIX}.enable{id}'

			full_command = f'{EXTENSION_ID}.{command}'

			description = f'Show button for command `{name}`.'
			if info:
				description += f' *{info}*'

			full_when = f'(config.{CONFIG_PREFIX}.enableAll || config.{config_name})'
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

			yield full_category, configuration_data, commands_data, menus_data

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
	buttons: dict = yaml.safe_load(BUTTONS_FILE.open('r'))

	package_data: dict = json.load(PACKAGE_FILE.open())

	configuration_categories = [config.get('id') for config in package_data['contributes']['configuration']]

	configuration = package_data['contributes']['configuration']
	for index, category in enumerate(configuration_categories):
		if category and category.startswith(CONFIG_CATEGORY_PREFIX):
			configuration[index]['properties'] = {}

	commands = package_data['contributes']['commands']
	commands = [item for item in commands if not item.get('generated')]

	menus = package_data['contributes']['menus']
	menus['scm/title'] = [item for item in menus['scm/title'] if not item.get('generated')]

	for configuration_category, configuration_data, commands_data, menus_data in parse_buttons(buttons, include):
		configuration_category_index = configuration_categories.index(configuration_category)
		configuration[configuration_category_index]['properties'].update([configuration_data])
		commands.append(commands_data)
		menus['scm/title'].append(menus_data)

	json.dump(package_data, PACKAGE_FILE.open('w', encoding='utf-8'), indent=4)


def main() -> None:
	enable_ansi_support()
	update_package()


if __name__ == "__main__":
	main()
