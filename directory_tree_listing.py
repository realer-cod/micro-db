import os
import argparse

def get_ignore_list(file_path, default_list):
    """
    Универсальная функция для чтения файла игнорирования.
    :param file_path: Путь к файлу.
    :param default_list: Стандартный список, если файл не найден.
    """
    if not os.path.exists(file_path):
        print(f"Файл '{file_path}' не найден. Используется стандартный список игнорирования.")
        return default_list
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ignored = {line.strip() for line in f if line.strip()}
            print(f"Загружен список игнорирования из '{file_path}'.")
            return ignored
    except IOError as e:
        print(f"Ошибка при чтении файла '{file_path}': {e}. Используется стандартный список.")
        return default_list

def generate_tree(start_path, ignore_list, prefix='', level=-1, max_level=None):
    """
    Генерирует строки для визуального дерева каталогов.
    """
    if max_level is not None and level >= max_level:
        return

    try:
        entries = sorted(
            [e for e in os.scandir(start_path) if e.name not in ignore_list],
            key=lambda e: e.name.lower()
        )
    except (FileNotFoundError, PermissionError):
        return

    dirs = [e for e in entries if e.is_dir()]
    files = [e for e in entries if e.is_file()]
    
    all_items = dirs + files

    for i, item in enumerate(all_items):
        is_last = (i == len(all_items) - 1)
        connector = '└───' if is_last else '├───'
        yield f"{prefix}{connector}{item.name}"
        if item.is_dir():
            new_prefix = prefix + ('    ' if is_last else '│   ')
            yield from generate_tree(item.path, ignore_list, new_prefix, level + 1, max_level)

def generate_listing(start_path, tree_ignore, listing_ignore, output_file_name):
    """
    Генерирует листинг содержимого файлов для LLM.
    """
    # Преобразуем список игнорирования в кортеж для .endswith()
    ignore_extensions = tuple(ext for ext in listing_ignore if ext.startswith('.'))

    for root, dirs, files in os.walk(start_path):
        # Исключаем папки из обхода, используя список tree_ignore
        dirs[:] = [d for d in dirs if d not in tree_ignore]
        
        for filename in files:
            # Проверяем, не находится ли файл или его расширение в списке игнорирования
            if filename in listing_ignore or filename.endswith(ignore_extensions):
                continue
            
            # Игнорируем сам файл вывода
            if os.path.abspath(os.path.join(root, filename)) == os.path.abspath(output_file_name):
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, start_path)
            
            yield f"\n# {'-'*5} START: {relative_path.replace(os.sep, '/')} {'-'*5}\n\n"
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    yield f.read()
            except Exception as e:
                yield f"# Ошибка чтения файла: {e}\n"
            yield f"\n# {'-'*5} END: {relative_path.replace(os.sep, '/')} {'-'*5}\n"

def main():
    parser = argparse.ArgumentParser(
        description="Создает дерево каталогов или листинг файлов для LLM.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('path', nargs='?', default='.', help='Путь к каталогу (по умолчанию: текущий).')
    parser.add_argument('-o', '--output', metavar='FILE', help='Сохранить вывод в указанный файл.')
    
    # Аргументы для режима дерева
    tree_group = parser.add_argument_group('Режим дерева каталогов')
    tree_group.add_argument('--ignore-tree-file', default='ignore_tree.txt', help='Файл для игнорирования папок/файлов в дереве.')
    tree_group.add_argument('-L', '--level', type=int, metavar='LEVEL', help='Максимальная глубина дерева.')

    # Аргументы для режима листинга
    listing_group = parser.add_argument_group('Режим листинга файлов')
    listing_group.add_argument('--listing', action='store_true', help='Активировать режим создания листинга файлов.')
    listing_group.add_argument('--ignore-listing-file', default='ignore_listing.txt', help='Файл для игнорирования файлов/расширений в листинге.')

    args = parser.parse_args()

    # Загрузка списков игнорирования
    default_tree_ignore = {'.git', '.idea', '__pycache__', '.venv', 'node_modules', 'dist', 'build'}
    tree_ignore_set = get_ignore_list(args.ignore_tree_file, default_tree_ignore)

    if args.listing:
        # --- РЕЖИМ ЛИСТИНГА ---
        if not args.output:
            print("Ошибка: для режима листинга необходимо указать выходной файл с помощью -o/--output.")
            return
            
        default_listing_ignore = {
            # Расширения
            '.pyc', '.pyo', '.pyd', '.log', '.tmp', '.DS_Store', '.swp', '.swo',
            '.exe', '.dll', '.so', '.o', '.a', '.lib', '.class', '.jar',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp', '.tif', '.tiff',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.tgz',
            '.db', '.sqlite', '.sqlite3', '.bak',
            # Конкретные файлы
            'poetry.lock', 'package-lock.json', 'yarn.lock', '.env'
        }
        listing_ignore_set = get_ignore_list(args.ignore_listing_file, default_listing_ignore)
        listing_generator = generate_listing(args.path, tree_ignore_set, listing_ignore_set, args.output)
        
        print(f"Создаю листинг файлов в: {args.output}...")
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                for content_part in listing_generator:
                    f.write(content_part)
            print("Готово!")
        except IOError as e:
            print(f"Не удалось записать в файл: {e}")

    else:
        # --- РЕЖИМ ДЕРЕВА ---
        tree_lines_generator = generate_tree(args.path, tree_ignore_set, level=0, max_level=args.level)
        header = f"Дерево для каталога: {os.path.abspath(args.path)}\n"
        root_line = f"{os.path.abspath(args.path)}"

        if args.output:
            print(f"Сохраняю дерево в файл: {args.output}...")
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(header)
                    f.write(root_line + '\n')
                    for line in tree_lines_generator:
                        f.write(line + '\n')
                print("Готово!")
            except IOError as e:
                print(f"Не удалось записать в файл: {e}")
        else:
            print("\n" + header)
            print(root_line)
            for line in tree_lines_generator:
                print(line)

if __name__ == '__main__':
    main()