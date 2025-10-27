#!/usr/bin/env python3
"""
Главный скрипт для запуска всех тестов системы оценки ERC-20 токенов
"""

import asyncio
import sys
import time
from pathlib import Path

def print_header():
    """Вывод заголовка"""
    print("=" * 80)
    print("🚀 СИСТЕМА ТЕСТИРОВАНИЯ ОЦЕНКИ ERC-20 ТОКЕНОВ")
    print("=" * 80)
    print("📋 Доступные тесты:")
    print("   1. test_evaluation.py - Базовые тесты системы")
    print("   2. test_specific_tokens.py - Тесты конкретных токенов")
    print("   3. test_real_data.py - Тесты с реальными данными")
    print("   4. examples.py - Примеры использования")
    print("=" * 80)

def run_test(test_file: str, description: str):
    """Запуск конкретного теста"""
    print(f"\n🔍 Запуск теста: {description}")
    print(f"📁 Файл: {test_file}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Импортируем и запускаем тест
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            print(f"❌ Файл {test_file} не найден")
            return False
        
        # Запускаем тест как модуль
        import subprocess
        result = subprocess.run([sys.executable, str(test_path)], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        
        # Выводим результат
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️  Предупреждения/ошибки:")
            print(result.stderr)
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Тест {description} завершен успешно за {elapsed_time:.2f}с")
            return True
        else:
            print(f"❌ Тест {description} завершился с ошибкой (код: {result.returncode})")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Ошибка запуска теста {description}: {e}")
        print(f"   Время выполнения: {elapsed_time:.2f}с")
        return False

async def run_all_tests():
    """Запуск всех тестов"""
    print_header()
    
    tests = [
        ("test_evaluation.py", "Базовые тесты системы"),
        ("test_specific_tokens.py", "Тесты конкретных токенов"),
        ("test_real_data.py", "Тесты с реальными данными")
    ]
    
    print(f"\n🚀 Начинаю выполнение {len(tests)} тестов...")
    
    results = []
    total_start_time = time.time()
    
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append({
            'test': description,
            'file': test_file,
            'success': success
        })
        
        # Небольшая пауза между тестами
        if test_file != tests[-1][0]:  # Не для последнего теста
            print("\n⏳ Пауза 2 секунды перед следующим тестом...")
            await asyncio.sleep(2)
    
    total_time = time.time() - total_start_time
    
    # Выводим итоговые результаты
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ УСПЕШНО" if result['success'] else "❌ НЕУДАЧНО"
        print(f"   {result['test']}: {status}")
    
    print(f"\n📈 Общая статистика:")
    print(f"   Всего тестов: {total}")
    print(f"   Успешно: {successful}")
    print(f"   Неудачно: {total - successful}")
    print(f"   Процент успеха: {(successful/total)*100:.1f}%")
    print(f"   Общее время: {total_time:.2f}с")
    
    if successful == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   Система оценки токенов работает корректно")
    else:
        print(f"\n⚠️  {total - successful} ТЕСТОВ НЕ ПРОЙДЕНО")
        print("   Рекомендуется проверить ошибки и исправить проблемы")
    
    return successful == total

def main():
    """Главная функция"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
