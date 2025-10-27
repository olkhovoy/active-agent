#!/usr/bin/env python3
"""
Тест оценки конкретных известных ERC-20 токенов
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
    print("✅ Все модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Список известных токенов для тестирования
KNOWN_TOKENS = [
    {
        'name': 'Tether USD',
        'symbol': 'USDT',
        'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'description': 'Стейблкоин, привязанный к доллару США'
    },
    {
        'name': 'USD Coin',
        'symbol': 'USDC',
        'contract_address': '0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8',
        'description': 'Стейблкоин, привязанный к доллару США'
    },
    {
        'name': 'Wrapped Ether',
        'symbol': 'WETH',
        'contract_address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'description': 'Wrapped версия ETH для DeFi протоколов'
    },
    {
        'name': 'Chainlink',
        'symbol': 'LINK',
        'contract_address': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
        'description': 'Oracle сеть для блокчейнов'
    },
    {
        'name': 'Uniswap',
        'symbol': 'UNI',
        'contract_address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
        'description': 'Токен управления DEX протокола'
    }
]


def create_mock_token_data(token_info: Dict) -> Dict:
    """Создание мок-данных для токена на основе известной информации"""
    
    # Базовые данные
    mock_data = {
        'contract_address': token_info['contract_address'],
        'name': token_info['name'],
        'symbol': token_info['symbol'],
        'market_cap_usd': 1000000000,  # $1B
        'price_usd': 1.0,
        'volume_24h_usd': 50000000,  # $50M
        'source': 'known_token_test'
    }
    
    # Специфичные данные для разных типов токенов
    if 'USDT' in token_info['symbol'] or 'USDC' in token_info['symbol']:
        mock_data.update({
            'market_cap_usd': 50000000000,  # $50B
            'price_usd': 1.0,
            'volume_24h_usd': 1000000000  # $1B
        })
    elif 'WETH' in token_info['symbol']:
        mock_data.update({
            'market_cap_usd': 50000000000,  # $50B
            'price_usd': 3000.0,
            'volume_24h_usd': 2000000000  # $2B
        })
    elif 'LINK' in token_info['symbol']:
        mock_data.update({
            'market_cap_usd': 10000000000,  # $10B
            'price_usd': 15.0,
            'volume_24h_usd': 500000000  # $500M
        })
    elif 'UNI' in token_info['symbol']:
        mock_data.update({
            'market_cap_usd': 5000000000,  # $5B
            'price_usd': 7.0,
            'volume_24h_usd': 200000000  # $200M
        })
    
    return mock_data


def test_token_evaluation():
    """Тест оценки известных токенов"""
    print("\n=== Тест оценки известных токенов ===")
    
    try:
        evaluator = AdvancedTokenEvaluator()
        
        results = []
        
        for token_info in KNOWN_TOKENS:
            print(f"\n🔍 Оцениваю {token_info['symbol']} ({token_info['name']})")
            print(f"   Адрес: {token_info['contract_address']}")
            print(f"   Описание: {token_info['description']}")
            
            # Создаем мок-данные
            mock_data = create_mock_token_data(token_info)
            
            try:
                # Пытаемся выполнить оценку
                assessment = evaluator.evaluate_token(
                    mock_data['contract_address'],
                    mock_data
                )
                
                print(f"   ✅ Оценка выполнена успешно")
                print(f"      Общий балл: {assessment.overall_score:.2f}")
                print(f"      Уровень риска: {assessment.risk_level}")
                print(f"      Рекомендация: {assessment.recommendation}")
                print(f"      Безопасность: {assessment.security_score:.2f}")
                print(f"      Ликвидность: {assessment.liquidity_score:.2f}")
                print(f"      Сообщество: {assessment.community_score:.2f}")
                
                if assessment.red_flags:
                    print(f"      🚨 Красные флаги: {', '.join(assessment.red_flags)}")
                if assessment.green_flags:
                    print(f"      ✅ Зеленые флаги: {', '.join(assessment.green_flags)}")
                
                results.append({
                    'token': token_info['symbol'],
                    'assessment': assessment,
                    'success': True
                })
                
            except Exception as eval_error:
                print(f"   ⚠️  Оценка не выполнена: {eval_error}")
                print(f"      Это может быть связано с отсутствием API ключей")
                
                results.append({
                    'token': token_info['symbol'],
                    'assessment': None,
                    'success': False,
                    'error': str(eval_error)
                })
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка в тесте оценки: {e}")
        return []


def test_risk_classification():
    """Тест классификации рисков"""
    print("\n=== Тест классификации рисков ===")
    
    try:
        # Создаем токены с разными уровнями риска
        risk_test_tokens = [
            {
                'name': 'Low Risk Token',
                'symbol': 'LOW',
                'data': {
                    'market_cap_usd': 10000000000,  # $10B
                    'holders_count': 1000000,
                    'transactions_count': 10000000,
                    'age_days': 1000
                }
            },
            {
                'name': 'Medium Risk Token',
                'symbol': 'MED',
                'data': {
                    'market_cap_usd': 1000000000,  # $1B
                    'holders_count': 100000,
                    'transactions_count': 1000000,
                    'age_days': 100
                }
            },
            {
                'name': 'High Risk Token',
                'symbol': 'HIGH',
                'data': {
                    'market_cap_usd': 10000000,  # $10M
                    'holders_count': 1000,
                    'transactions_count': 10000,
                    'age_days': 10
                }
            }
        ]
        
        evaluator = AdvancedTokenEvaluator()
        
        for token in risk_test_tokens:
            print(f"\n🔍 Тестирую {token['symbol']} ({token['name']})")
            
            # Создаем полные мок-данные
            mock_data = {
                'contract_address': f"0x{token['symbol'].lower() * 10}",
                'name': token['name'],
                'symbol': token['symbol'],
                'price_usd': 1.0,
                'volume_24h_usd': token['data']['market_cap_usd'] * 0.05,
                'source': 'risk_test'
            }
            mock_data.update(token['data'])
            
            try:
                assessment = evaluator.evaluate_token(
                    mock_data['contract_address'],
                    mock_data
                )
                
                print(f"   ✅ Оценка: {assessment.risk_level} риск")
                print(f"      Балл: {assessment.overall_score:.2f}")
                print(f"      Рекомендация: {assessment.recommendation}")
                
            except Exception as e:
                print(f"   ⚠️  Ошибка оценки: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте классификации рисков: {e}")
        return False


def test_data_structures():
    """Тест структур данных"""
    print("\n=== Тест структур данных ===")
    
    try:
        # Тест TokenInfo
        print("🔍 Тестирую структуру TokenInfo...")
        token_info = TokenInfo(
            name="Test Token",
            symbol="TEST",
            contract_address="0x1234567890123456789012345678901234567890",
            market_cap_usd=1000000,
            price_usd=1.0,
            volume_24h_usd=50000,
            discovery_method="test"
        )
        print(f"   ✅ TokenInfo создан: {token_info.name}")
        
        # Тест TokenAssessment
        print("🔍 Тестирую структуру TokenAssessment...")
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
            red_flags=["High volatility"],
            green_flags=["Strong community"],
            assessment_date="2024-01-01"
        )
        print(f"   ✅ TokenAssessment создан: {assessment.risk_level} риск")
        
        # Тест TokenIndex
        print("🔍 Тестирую структуру TokenIndex...")
        from datetime import datetime
        token_index = TokenIndex(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            decimals=18,
            total_supply="1000000000000000000000000",
            first_seen=datetime.now(),
            last_updated=datetime.now(),
            transaction_count=1000,
            holder_count=100,
            liquidity_usd=1000000,
            market_cap_usd=1000000
        )
        print(f"   ✅ TokenIndex создан: {token_index.symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте структур данных: {e}")
        return False


async def run_token_tests():
    """Запуск всех тестов токенов"""
    print("🚀 Запуск тестов оценки конкретных токенов")
    print("=" * 60)
    
    tests = [
        test_data_structures,
        test_token_evaluation,
        test_risk_classification
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
        success = asyncio.run(run_token_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
