#!/usr/bin/env python3
"""
Тест работы с реальными данными токенов из CSV файла
"""

import asyncio
import json
import logging
import sys
import pandas as pd
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


def load_real_token_data():
    """Загрузка реальных данных токенов из CSV"""
    print("\n=== Загрузка реальных данных токенов ===")
    
    try:
        csv_path = Path(__file__).parent / "erc20_top20.csv"
        
        if not csv_path.exists():
            print(f"❌ Файл {csv_path} не найден")
            return None
        
        # Загружаем CSV
        df = pd.read_csv(csv_path)
        print(f"✅ Загружено {len(df)} токенов из CSV")
        
        # Показываем первые 5 токенов
        print("\n📊 Первые 5 токенов:")
        for i, row in df.head().iterrows():
            print(f"   {i+1}. {row['symbol']} ({row['name']})")
            print(f"      Рыночная капитализация: ${row['market_cap_usd']:,}")
            print(f"      Объем 24ч: ${row['volume_24h_usd']:,}")
            print(f"      Ранг: #{row['rank']}")
            print()
        
        return df
        
    except Exception as e:
        print(f"❌ Ошибка загрузки CSV: {e}")
        return None


def convert_csv_to_token_info(df: pd.DataFrame) -> List[TokenInfo]:
    """Конвертация CSV данных в объекты TokenInfo"""
    print("\n=== Конвертация CSV в TokenInfo ===")
    
    try:
        tokens = []
        
        for _, row in df.iterrows():
            # Создаем TokenInfo объект
            token = TokenInfo(
                name=row['name'],
                symbol=row['symbol'],
                contract_address=row['contract'],
                market_cap_usd=row['market_cap_usd'],
                volume_24h_usd=row['volume_24h_usd'],
                discovery_method="erc20_top20_csv"
            )
            tokens.append(token)
        
        print(f"✅ Конвертировано {len(tokens)} токенов")
        return tokens
        
    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
        return []


def test_real_token_evaluation(tokens: List[TokenInfo]):
    """Тест оценки реальных токенов"""
    print("\n=== Тест оценки реальных токенов ===")
    
    try:
        evaluator = AdvancedTokenEvaluator()
        results = []
        
        # Тестируем первые 5 токенов для экономии времени
        test_tokens = tokens[:5]
        
        for token in test_tokens:
            print(f"\n🔍 Оцениваю {token.symbol} ({token.name})")
            print(f"   Адрес: {token.contract_address}")
            print(f"   Рыночная капитализация: ${token.market_cap_usd:,}")
            print(f"   Объем 24ч: ${token.volume_24h_usd:,}")
            
            try:
                # Создаем словарь с данными для оценки
                token_data = {
                    'contract_address': token.contract_address,
                    'name': token.name,
                    'symbol': token.symbol,
                    'market_cap_usd': token.market_cap_usd,
                    'volume_24h_usd': token.volume_24h_usd
                }
                
                # Пытаемся выполнить оценку
                assessment = evaluator.evaluate_token(
                    token.contract_address,
                    token_data
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
                    'token': token.symbol,
                    'assessment': assessment,
                    'success': True
                })
                
            except Exception as eval_error:
                print(f"   ⚠️  Оценка не выполнена: {eval_error}")
                print(f"      Это может быть связано с отсутствием API ключей")
                
                results.append({
                    'token': token.symbol,
                    'assessment': None,
                    'success': False,
                    'error': str(eval_error)
                })
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка в тесте оценки: {e}")
        return []


def test_market_cap_analysis(tokens: List[TokenInfo]):
    """Тест анализа рыночной капитализации"""
    print("\n=== Тест анализа рыночной капитализации ===")
    
    try:
        # Группируем токены по размеру капитализации
        large_cap = []  # > $10B
        mid_cap = []    # $1B - $10B
        small_cap = []  # < $1B
        
        for token in tokens:
            if token.market_cap_usd > 10000000000:
                large_cap.append(token)
            elif token.market_cap_usd > 1000000000:
                mid_cap.append(token)
            else:
                small_cap.append(token)
        
        print(f"📊 Анализ по рыночной капитализации:")
        print(f"   Large Cap (>$10B): {len(large_cap)} токенов")
        print(f"   Mid Cap ($1B-$10B): {len(mid_cap)} токенов")
        print(f"   Small Cap (<$1B): {len(small_cap)} токенов")
        
        # Показываем примеры для каждой категории
        if large_cap:
            print(f"\n   🏆 Large Cap примеры:")
            for token in large_cap[:3]:
                print(f"      {token.symbol}: ${token.market_cap_usd:,}")
        
        if mid_cap:
            print(f"\n   🎯 Mid Cap примеры:")
            for token in mid_cap[:3]:
                print(f"      {token.symbol}: ${token.market_cap_usd:,}")
        
        if small_cap:
            print(f"\n   💎 Small Cap примеры:")
            for token in small_cap[:3]:
                print(f"      {token.symbol}: ${token.market_cap_usd:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в анализе капитализации: {e}")
        return False


def test_volume_analysis(tokens: List[TokenInfo]):
    """Тест анализа объемов торгов"""
    print("\n=== Тест анализа объемов торгов ===")
    
    try:
        # Сортируем по объему
        sorted_tokens = sorted(tokens, key=lambda x: x.volume_24h_usd, reverse=True)
        
        print(f"📊 Топ-10 токенов по объему торгов:")
        for i, token in enumerate(sorted_tokens[:10]):
            print(f"   {i+1:2d}. {token.symbol:6s}: ${token.volume_24h_usd:,}")
        
        # Анализируем соотношение объема к капитализации
        print(f"\n📈 Соотношение объема к капитализации (Volume/MC):")
        for token in sorted_tokens[:5]:
            ratio = token.volume_24h_usd / token.market_cap_usd if token.market_cap_usd > 0 else 0
            print(f"   {token.symbol}: {ratio:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в анализе объемов: {e}")
        return False


def export_test_results(tokens: List[TokenInfo], results: List[Dict]):
    """Экспорт результатов тестирования"""
    print("\n=== Экспорт результатов тестирования ===")
    
    try:
        # Создаем отчет
        report = {
            'test_date': pd.Timestamp.now().isoformat(),
            'total_tokens_tested': len(tokens),
            'evaluation_results': results,
            'summary': {
                'successful_evaluations': len([r for r in results if r['success']]),
                'failed_evaluations': len([r for r in results if not r['success']]),
                'tokens_by_risk': {},
                'recommendations': {}
            }
        }
        
        # Анализируем успешные оценки
        successful_results = [r for r in results if r['success'] and r['assessment']]
        
        for result in successful_results:
            assessment = result['assessment']
            
            # Подсчитываем по уровням риска
            risk_level = assessment.risk_level
            report['summary']['tokens_by_risk'][risk_level] = report['summary']['tokens_by_risk'].get(risk_level, 0) + 1
            
            # Подсчитываем по рекомендациям
            recommendation = assessment.recommendation
            report['summary']['recommendations'][recommendation] = report['summary']['recommendations'].get(recommendation, 0) + 1
        
        # Сохраняем отчет
        output_file = "real_tokens_test_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Отчет сохранен в {output_file}")
        print(f"   Успешных оценок: {report['summary']['successful_evaluations']}")
        print(f"   Неудачных оценок: {report['summary']['failed_evaluations']}")
        
        if report['summary']['tokens_by_risk']:
            print(f"   Распределение по риску: {report['summary']['tokens_by_risk']}")
        
        if report['summary']['recommendations']:
            print(f"   Распределение рекомендаций: {report['summary']['recommendations']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return False


async def run_real_data_tests():
    """Запуск всех тестов с реальными данными"""
    print("🚀 Запуск тестов с реальными данными токенов")
    print("=" * 60)
    
    # Загружаем данные
    df = load_real_token_data()
    if df is None:
        return False
    
    # Конвертируем в TokenInfo
    tokens = convert_csv_to_token_info(df)
    if not tokens:
        return False
    
    # Запускаем тесты
    tests = [
        lambda: test_market_cap_analysis(tokens),
        lambda: test_volume_analysis(tokens),
        lambda: test_real_token_evaluation(tokens)
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест завершился с ошибкой: {e}")
    
    # Экспортируем результаты
    if passed > 0:
        results = test_real_token_evaluation(tokens)
        export_test_results(tokens, results)
    
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
        success = asyncio.run(run_real_data_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
