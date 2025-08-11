#!/usr/bin/env python3
"""
Примеры использования системы оценки ERC-20 токенов
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict

# Импорт наших модулей
from token_discovery_agent import TokenDiscoveryAgent, TokenInfo
from advanced_evaluator import AdvancedTokenEvaluator, TokenAssessment
from token_monitor import TokenMonitor, TokenIndex
from token_evaluation_system import TokenEvaluationSystem

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_discovery_only():
    """Пример 1: Только обнаружение новых токенов"""
    print("\n=== Пример 1: Обнаружение новых токенов ===")
    
    agent = TokenDiscoveryAgent()
    
    # Обнаружение через CoinGecko
    print("Обнаружение через CoinGecko...")
    coingecko_tokens = agent.discover_new_tokens_coingecko(
        min_market_cap=5000000,  # $5M
        max_age_days=14
    )
    print(f"Найдено {len(coingecko_tokens)} токенов через CoinGecko")
    
    # Обнаружение через Etherscan
    print("Обнаружение через Etherscan...")
    etherscan_tokens = agent.discover_new_tokens_etherscan(
        min_holders=500,
        min_transactions=2000
    )
    print(f"Найдено {len(etherscan_tokens)} токенов через Etherscan")
    
    # Сохранение результатов
    all_tokens = coingecko_tokens + etherscan_tokens
    if all_tokens:
        agent.save_discovered_tokens(all_tokens, "example_discovery.csv")
        print(f"Всего обнаружено {len(all_tokens)} токенов")
        
        # Показать первые 5 токенов
        for i, token in enumerate(all_tokens[:5]):
            print(f"  {i+1}. {token.symbol} ({token.name}) - {token.contract_address[:10]}...")


async def example_2_evaluation_only():
    """Пример 2: Только оценка конкретных токенов"""
    print("\n=== Пример 2: Оценка конкретных токенов ===")
    
    evaluator = AdvancedTokenEvaluator()
    
    # Список токенов для оценки (примеры)
    test_tokens = [
        {
            'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT
            'name': 'Tether USD',
            'symbol': 'USDT'
        },
        {
            'contract_address': '0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8',  # USDC
            'name': 'USD Coin',
            'symbol': 'USDC'
        }
    ]
    
    for token_data in test_tokens:
        print(f"Оцениваю {token_data['symbol']}...")
        
        try:
            assessment = evaluator.evaluate_token(
                token_data['contract_address'],
                token_data
            )
            
            print(f"  Результат: {assessment.recommendation}")
            print(f"  Общий балл: {assessment.overall_score:.2f}")
            print(f"  Уровень риска: {assessment.risk_level}")
            print(f"  Безопасность: {assessment.security_score:.2f}")
            print(f"  Ликвидность: {assessment.liquidity_score:.2f}")
            print(f"  Сообщество: {assessment.community_score:.2f}")
            
            if assessment.red_flags:
                print(f"  Красные флаги: {', '.join(assessment.red_flags)}")
            if assessment.green_flags:
                print(f"  Зеленые флаги: {', '.join(assessment.green_flags)}")
                
        except Exception as e:
            print(f"  Ошибка оценки: {e}")
        
        print()


async def example_3_monitoring_only():
    """Пример 3: Только мониторинг токенов"""
    print("\n=== Пример 3: Мониторинг токенов ===")
    
    monitor = TokenMonitor("example_monitor.db")
    
    # Инициализация базы данных
    monitor.init_database()
    
    # Добавление тестовых токенов
    test_tokens = [
        TokenIndex(
            contract_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            name="Tether USD",
            symbol="USDT",
            decimals=6,
            total_supply="1000000000000000",
            first_seen=monitor._get_current_time(),
            last_updated=monitor._get_current_time(),
            transaction_count=1000000,
            holder_count=5000000,
            liquidity_usd=50000000000,
            market_cap_usd=95000000000,
            is_scam=False,
            risk_score=0.1
        )
    ]
    
    for token in test_tokens:
        await monitor.save_token_to_db(token)
        print(f"Добавлен токен: {token.symbol}")
    
    # Получение токенов по уровню риска
    high_risk_tokens = monitor.get_tokens_by_risk(risk_threshold=0.5)
    print(f"Токенов с высоким риском: {len(high_risk_tokens)}")
    
    # Экспорт в CSV
    monitor.export_tokens_to_csv("example_monitored_tokens.csv")
    print("Данные экспортированы в CSV")


async def example_4_full_system():
    """Пример 4: Полная система оценки"""
    print("\n=== Пример 4: Полная система оценки ===")
    
    # Создание системы с кастомной конфигурацией
    config = {
        'discovery': {
            'min_market_cap': 2000000,  # $2M
            'max_age_days': 21,
            'min_holders': 200,
            'min_transactions': 1500
        },
        'evaluation': {
            'security_weight': 0.5,
            'liquidity_weight': 0.3,
            'community_weight': 0.2,
            'risk_threshold': 0.6
        }
    }
    
    system = TokenEvaluationSystem(config)
    
    try:
        # Запуск полного цикла
        print("Запуск полного цикла оценки...")
        await system.run_full_evaluation_cycle()
        
        # Получение отчета
        report = system.get_summary_report()
        print("\nСводный отчет:")
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        
        # Экспорт данных
        system.export_all_data("example_full_system_export")
        print("\nДанные экспортированы")
        
        # Остановка мониторинга
        await system.stop_monitoring()
        
    except Exception as e:
        print(f"Ошибка в полной системе: {e}")
        await system.stop_monitoring()


async def example_5_batch_evaluation():
    """Пример 5: Пакетная оценка токенов из CSV"""
    print("\n=== Пример 5: Пакетная оценка из CSV ===")
    
    # Проверяем, есть ли файл с токенами
    csv_file = "erc20_top20.csv"
    if not Path(csv_file).exists():
        print(f"Файл {csv_file} не найден. Создаю тестовые данные...")
        
        # Создаем тестовые данные
        test_data = [
            ["Test Token 1", "TEST1", "0x1234567890123456789012345678901234567890", 1000000, 1000000, 50000, 1],
            ["Test Token 2", "TEST2", "0x2345678901234567890123456789012345678901", 2000000, 2000000, 75000, 2],
            ["Test Token 3", "TEST3", "0x3456789012345678901234567890123456789012", 3000000, 3000000, 100000, 3]
        ]
        
        import pandas as pd
        df = pd.DataFrame(test_data, columns=['name', 'symbol', 'contract', 'market_cap_usd', 'fdv_usd', 'volume_24h_usd', 'rank'])
        df.to_csv(csv_file, index=False)
        print(f"Создан тестовый файл {csv_file}")
    
    # Читаем токены из CSV
    import pandas as pd
    df = pd.read_csv(csv_file)
    
    evaluator = AdvancedTokenEvaluator()
    results = []
    
    print(f"Оцениваю {len(df)} токенов...")
    
    for index, row in df.iterrows():
        token_data = {
            'name': row['name'],
            'symbol': row['symbol'],
            'market_cap_usd': row['market_cap_usd'],
            'volume_24h_usd': row['volume_24h_usd']
        }
        
        print(f"  {index+1}/{len(df)}: {row['symbol']}")
        
        try:
            assessment = evaluator.evaluate_token(
                row['contract'],
                token_data
            )
            
            results.append({
                'symbol': row['symbol'],
                'name': row['name'],
                'contract': row['contract'],
                'recommendation': assessment.recommendation,
                'risk_level': assessment.risk_level,
                'overall_score': assessment.overall_score,
                'red_flags': assessment.red_flags or []
            })
            
        except Exception as e:
            print(f"    Ошибка: {e}")
            results.append({
                'symbol': row['symbol'],
                'name': row['name'],
                'contract': row['contract'],
                'recommendation': 'ERROR',
                'risk_level': 'UNKNOWN',
                'overall_score': 0.0,
                'red_flags': [f"Ошибка оценки: {e}"]
            })
    
    # Сохранение результатов
    results_df = pd.DataFrame(results)
    results_df.to_csv("batch_evaluation_results.csv", index=False)
    print(f"\nРезультаты сохранены в batch_evaluation_results.csv")
    
    # Статистика
    recommendations = results_df['recommendation'].value_counts()
    risk_levels = results_df['risk_level'].value_counts()
    
    print("\nСтатистика:")
    print("Рекомендации:")
    for rec, count in recommendations.items():
        print(f"  {rec}: {count}")
    
    print("\nУровни риска:")
    for risk, count in risk_levels.items():
        print(f"  {risk}: {count}")


async def example_6_risk_analysis():
    """Пример 6: Анализ рисков и генерация отчетов"""
    print("\n=== Пример 6: Анализ рисков ===")
    
    # Создаем тестовые оценки
    test_assessments = [
        TokenAssessment(
            contract_address="0x1234567890123456789012345678901234567890",
            name="High Risk Token",
            symbol="HRT",
            overall_score=0.3,
            security_score=0.2,
            liquidity_score=0.4,
            community_score=0.3,
            risk_level="HIGH",
            recommendation="AVOID",
            red_flags=["Неверифицированный контракт", "Функция mint", "Высокая концентрация держателей"],
            green_flags=[],
            assessment_date="2024-01-01"
        ),
        TokenAssessment(
            contract_address="0x2345678901234567890123456789012345678901",
            name="Safe Token",
            symbol="SAFE",
            overall_score=0.8,
            security_score=0.9,
            liquidity_score=0.8,
            community_score=0.7,
            risk_level="LOW",
            recommendation="INVEST",
            red_flags=[],
            green_flags=["Верифицированный контракт", "Аудит проведен", "Мультисиг кошелек"],
            assessment_date="2024-01-01"
        )
    ]
    
    # Анализ распределения рисков
    risk_distribution = {}
    recommendation_distribution = {}
    
    for assessment in test_assessments:
        # Распределение по риску
        risk_level = assessment.risk_level
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Распределение по рекомендациям
        recommendation = assessment.recommendation
        recommendation_distribution[recommendation] = recommendation_distribution.get(recommendation, 0) + 1
    
    print("Распределение по уровням риска:")
    for risk, count in risk_distribution.items():
        print(f"  {risk}: {count}")
    
    print("\nРаспределение по рекомендациям:")
    for rec, count in recommendation_distribution.items():
        print(f"  {rec}: {count}")
    
    # Анализ красных флагов
    all_red_flags = []
    for assessment in test_assessments:
        if assessment.red_flags:
            all_red_flags.extend(assessment.red_flags)
    
    if all_red_flags:
        from collections import Counter
        red_flags_count = Counter(all_red_flags)
        
        print("\nТоп красных флагов:")
        for flag, count in red_flags_count.most_common():
            print(f"  {flag}: {count}")
    
    # Сохранение отчета
    report = {
        'analysis_date': '2024-01-01',
        'total_tokens': len(test_assessments),
        'risk_distribution': risk_distribution,
        'recommendation_distribution': recommendation_distribution,
        'red_flags_analysis': dict(red_flags_count) if all_red_flags else {},
        'high_risk_tokens': [
            {
                'symbol': t.symbol,
                'name': t.name,
                'contract': t.contract_address,
                'risk_level': t.risk_level,
                'red_flags': t.red_flags
            }
            for t in test_assessments if t.risk_level in ['HIGH', 'CRITICAL']
        ]
    }
    
    with open('risk_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nОтчет по анализу рисков сохранен в risk_analysis_report.json")


def main():
    """Главная функция для запуска примеров"""
    print("Примеры использования системы оценки ERC-20 токенов")
    print("=" * 60)
    
    # Список доступных примеров
    examples = [
        ("1", "Только обнаружение новых токенов", example_1_discovery_only),
        ("2", "Только оценка конкретных токенов", example_2_evaluation_only),
        ("3", "Только мониторинг токенов", example_3_monitoring_only),
        ("4", "Полная система оценки", example_4_full_system),
        ("5", "Пакетная оценка токенов из CSV", example_5_batch_evaluation),
        ("6", "Анализ рисков и генерация отчетов", example_6_risk_analysis)
    ]
    
    print("Доступные примеры:")
    for num, desc, _ in examples:
        print(f"  {num}. {desc}")
    
    print("\nДля запуска всех примеров введите 'all'")
    print("Для запуска конкретного примера введите его номер")
    print("Для выхода введите 'quit'")
    
    while True:
        choice = input("\nВаш выбор: ").strip().lower()
        
        if choice == 'quit':
            print("До свидания!")
            break
        elif choice == 'all':
            print("\nЗапуск всех примеров...")
            for num, desc, func in examples:
                print(f"\n--- Запуск примера {num}: {desc} ---")
                try:
                    asyncio.run(func())
                except Exception as e:
                    print(f"Ошибка в примере {num}: {e}")
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            num = int(choice)
            desc, func = examples[num-1][1], examples[num-1][2]
            print(f"\n--- Запуск примера {num}: {desc} ---")
            try:
                asyncio.run(func())
            except Exception as e:
                print(f"Ошибка в примере {num}: {e}")
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
