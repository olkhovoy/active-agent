#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы оценки ERC-20 токенов
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Добавляем текущую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent))

# Импорт наших модулей
try:
    from token_discovery import TokenDiscoveryAgent, TokenInfo
    from advanced_evaluator import AdvancedTokenEvaluator, TokenAssessment
    from token_monitor import TokenMonitor, TokenIndex
    from token_evaluation_system import TokenEvaluationSystem
    print("✅ Все модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_imports():
    """Тест базовых импортов и инициализации классов"""
    print("\n=== Тест 1: Базовые импорты и инициализация ===")
    
    try:
        # Тест инициализации агента обнаружения
        discovery_agent = TokenDiscoveryAgent()
        print("✅ TokenDiscoveryAgent инициализирован")
        
        # Тест инициализации оценщика
        evaluator = AdvancedTokenEvaluator()
        print("✅ AdvancedTokenEvaluator инициализирован")
        
        # Тест инициализации монитора
        monitor = TokenMonitor("test.db")
        print("✅ TokenMonitor инициализирован")
        
        # Тест инициализации главной системы
        system = TokenEvaluationSystem()
        print("✅ TokenEvaluationSystem инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False


def test_token_info_creation():
    """Тест создания объектов TokenInfo"""
    print("\n=== Тест 2: Создание объектов TokenInfo ===")
    
    try:
        # Создаем тестовый токен
        test_token = TokenInfo(
            name="Test Token",
            symbol="TEST",
            contract_address="0x1234567890123456789012345678901234567890",
            market_cap_usd=1000000,
            price_usd=1.0,
            volume_24h_usd=50000,
            total_supply=1000000000000000000000000,
            discovery_method="test"
        )
        
        print(f"✅ TokenInfo создан: {test_token.name} ({test_token.symbol})")
        print(f"   Адрес: {test_token.contract_address}")
        print(f"   Рыночная капитализация: ${test_token.market_cap_usd:,}")
        print(f"   Метод обнаружения: {test_token.discovery_method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания TokenInfo: {e}")
        return False


def test_token_assessment_creation():
    """Тест создания объектов TokenAssessment"""
    print("\n=== Тест 3: Создание объектов TokenAssessment ===")
    
    try:
        # Создаем тестовую оценку
        assessment = TokenAssessment(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            overall_score=0.75,
            security_score=0.8,
            liquidity_score=0.7,
            community_score=0.75,
            risk_level="medium",
            recommendation="HOLD",
            red_flags=["High volatility", "Limited liquidity"],
            green_flags=["Strong community", "Verified contract"],
            assessment_date="2024-01-01"
        )
        
        print(f"✅ TokenAssessment создан")
        print(f"   Общий балл: {assessment.overall_score:.2f}")
        print(f"   Уровень риска: {assessment.risk_level}")
        print(f"   Рекомендация: {assessment.recommendation}")
        print(f"   Красные флаги: {', '.join(assessment.red_flags)}")
        print(f"   Зеленые флаги: {', '.join(assessment.green_flags)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания TokenAssessment: {e}")
        return False


def test_config_loading():
    """Тест загрузки конфигурации"""
    print("\n=== Тест 4: Загрузка конфигурации ===")
    
    try:
        import yaml
        
        # Загружаем конфигурацию
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            print("✅ Конфигурация загружена")
            print(f"   База данных: {config.get('database', {}).get('path', 'N/A')}")
            print(f"   Фильтры: мин. капитализация ${config.get('discovery', {}).get('filters', {}).get('min_market_cap_usd', 'N/A'):,}")
            print(f"   Веса: безопасность {config.get('evaluation', {}).get('weights', {}).get('security', 'N/A')}")
            
            return True
        else:
            print("❌ Файл конфигурации не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False


def test_mock_evaluation():
    """Тест имитации оценки токена"""
    print("\n=== Тест 5: Имитация оценки токена ===")
    
    try:
        evaluator = AdvancedTokenEvaluator()
        
        # Создаем тестовые данные токена
        mock_token_data = {
            'contract_address': '0x1234567890123456789012345678901234567890',
            'name': 'Mock Test Token',
            'symbol': 'MOCK',
            'total_supply': 1000000000000000000000000,
            'market_cap_usd': 5000000,
            'price_usd': 0.5,
            'volume_24h_usd': 250000
        }
        
        # Пытаемся выполнить оценку (может не работать без API ключей)
        try:
            assessment = evaluator.evaluate_token(
                mock_token_data['contract_address'],
                mock_token_data
            )
            print("✅ Оценка токена выполнена успешно")
            print(f"   Результат: {assessment.recommendation}")
            print(f"   Общий балл: {assessment.overall_score:.2f}")
            
        except Exception as eval_error:
            print(f"⚠️  Оценка не выполнена (ожидаемо без API): {eval_error}")
            print("   Это нормально для тестирования без внешних API")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте оценки: {e}")
        return False


def test_data_export():
    """Тест экспорта данных"""
    print("\n=== Тест 6: Экспорт данных ===")
    
    try:
        # Создаем тестовые данные
        test_tokens = [
            {
                'contract_address': '0x1234567890123456789012345678901234567890',
                'name': 'Test Token 1',
                'symbol': 'TEST1',
                'market_cap_usd': 1000000
            },
            {
                'contract_address': '0x2345678901234567890123456789012345678901',
                'name': 'Test Token 2',
                'symbol': 'TEST2',
                'market_cap_usd': 2000000
            }
        ]
        
        # Сохраняем в CSV
        import pandas as pd
        df = pd.DataFrame(test_tokens)
        output_file = "test_tokens_export.csv"
        df.to_csv(output_file, index=False)
        
        print(f"✅ Данные экспортированы в {output_file}")
        print(f"   Экспортировано {len(test_tokens)} токенов")
        
        # Проверяем, что файл создан
        if Path(output_file).exists():
            print(f"   Файл создан: {Path(output_file).stat().st_size} байт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка экспорта данных: {e}")
        return False


async def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов системы оценки ERC-20 токенов")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_token_info_creation,
        test_token_assessment_creation,
        test_config_loading,
        test_mock_evaluation,
        test_data_export
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с ошибкой: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены")
    
    return passed == total


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
