import os
import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd

# Импорт наших агентов
from token_discovery_agent import TokenDiscoveryAgent, TokenInfo
from advanced_evaluator import AdvancedTokenEvaluator, TokenAssessment
from token_monitor import TokenMonitor, TokenIndex, TokenEvent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TokenEvaluationSystem:
    """
    Главная система для комплексной оценки ERC-20 токенов.
    Объединяет обнаружение, оценку и мониторинг токенов.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Инициализация агентов
        self.discovery_agent = TokenDiscoveryAgent()
        self.evaluator = AdvancedTokenEvaluator()
        self.monitor = TokenMonitor(self.config.get('db_path', 'token_evaluation.db'))
        
        # Результаты работы
        self.discovered_tokens: List[TokenInfo] = []
        self.evaluated_tokens: List[TokenAssessment] = []
        self.monitored_tokens: List[TokenIndex] = []
        
        # Статистика
        self.stats = {
            'tokens_discovered': 0,
            'tokens_evaluated': 0,
            'tokens_monitored': 0,
            'scams_detected': 0,
            'high_risk_tokens': 0,
            'last_update': None
        }
    
    def _get_default_config(self) -> Dict:
        """Получение конфигурации по умолчанию"""
        return {
            'db_path': 'token_evaluation.db',
            'discovery': {
                'min_market_cap': 1000000,  # $1M
                'max_age_days': 30,
                'min_holders': 100,
                'min_transactions': 1000
            },
            'evaluation': {
                'security_weight': 0.4,
                'liquidity_weight': 0.3,
                'community_weight': 0.3,
                'risk_threshold': 0.7
            },
            'monitoring': {
                'block_interval': 100,
                'update_frequency_minutes': 30,
                'cleanup_days': 7
            }
        }
    
    async def run_full_evaluation_cycle(self):
        """Запуск полного цикла оценки токенов"""
        logger.info("Запуск полного цикла оценки токенов")
        
        try:
            # 1. Обнаружение новых токенов
            await self.discover_new_tokens()
            
            # 2. Оценка обнаруженных токенов
            await self.evaluate_discovered_tokens()
            
            # 3. Запуск мониторинга
            await self.start_monitoring()
            
            # 4. Обновление статистики
            self._update_stats()
            
            logger.info("Полный цикл оценки завершен успешно")
            
        except Exception as e:
            logger.error(f"Ошибка в цикле оценки: {e}")
            raise
    
    async def discover_new_tokens(self):
        """Обнаружение новых токенов через различные источники"""
        logger.info("Начинаю обнаружение новых токенов...")
        
        # Обнаружение через CoinGecko
        try:
            coingecko_tokens = self.discovery_agent.discover_new_tokens_coingecko(
                min_market_cap=self.config['discovery']['min_market_cap'],
                max_age_days=self.config['discovery']['max_age_days']
            )
            logger.info(f"Обнаружено {len(coingecko_tokens)} токенов через CoinGecko")
            self.discovered_tokens.extend(coingecko_tokens)
        except Exception as e:
            logger.warning(f"Ошибка при обнаружении через CoinGecko: {e}")
        
        # Обнаружение через Etherscan
        try:
            etherscan_tokens = self.discovery_agent.discover_tokens_etherscan(
                min_holders=self.config['discovery']['min_holders'],
                min_transactions=self.config['discovery']['min_transactions']
            )
            logger.info(f"Обнаружено {len(etherscan_tokens)} токенов через Etherscan")
            self.discovered_tokens.extend(etherscan_tokens)
        except Exception as e:
            logger.warning(f"Ошибка при обнаружении через Etherscan: {e}")
        
        # Удаление дубликатов
        self._remove_duplicates()
        
        # Сохранение результатов
        if self.discovered_tokens:
            self.discovery_agent.save_discovered_tokens(
                self.discovered_tokens, 
                f"discovered_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        
        logger.info(f"Всего обнаружено уникальных токенов: {len(self.discovered_tokens)}")
    
    async def evaluate_discovered_tokens(self):
        """Оценка обнаруженных токенов"""
        if not self.discovered_tokens:
            logger.info("Нет токенов для оценки")
            return
        
        logger.info(f"Начинаю оценку {len(self.discovered_tokens)} токенов...")
        
        for i, token in enumerate(self.discovered_tokens):
            try:
                logger.info(f"Оцениваю токен {i+1}/{len(self.discovered_tokens)}: {token.symbol} ({token.contract_address})")
                
                # Получение дополнительных данных для оценки
                token_data = await self._get_token_data_for_evaluation(token)
                
                # Выполнение оценки
                assessment = self.evaluator.evaluate_token(
                    token.contract_address, 
                    token_data
                )
                
                self.evaluated_tokens.append(assessment)
                
                # Небольшая задержка между запросами
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка при оценке токена {token.symbol}: {e}")
                continue
        
        # Сохранение результатов оценки
        self._save_evaluation_results()
        
        logger.info(f"Оценка завершена. Оценено токенов: {len(self.evaluated_tokens)}")
    
    async def _get_token_data_for_evaluation(self, token: TokenInfo) -> Dict:
        """Получение дополнительных данных для оценки токена"""
        token_data = {
            'name': token.name,
            'symbol': token.symbol,
            'market_cap_usd': token.market_cap_usd,
            'volume_24h_usd': token.volume_24h_usd,
            'price_usd': token.price_usd,
            'total_supply': token.total_supply,
            'circulating_supply': token.circulating_supply,
            'launch_date': token.launch_date,
            'platform': token.platform
        }
        
        # Попытка получить дополнительные данные из мониторинга
        try:
            monitored_token = await self.monitor.get_token_info(token.contract_address)
            if monitored_token:
                token_data.update({
                    'holder_count': monitored_token.holder_count,
                    'transaction_count': monitored_token.transaction_count,
                    'liquidity_usd': monitored_token.liquidity_usd,
                    'risk_score': monitored_token.risk_score
                })
        except Exception as e:
            logger.debug(f"Не удалось получить данные мониторинга для {token.symbol}: {e}")
        
        return token_data
    
    async def start_monitoring(self):
        """Запуск системы мониторинга"""
        logger.info("Запускаю систему мониторинга...")
        
        try:
            # Запуск мониторинга в фоновом режиме
            await self.monitor.start_monitoring()
            logger.info("Система мониторинга запущена")
            
        except Exception as e:
            logger.error(f"Ошибка при запуске мониторинга: {e}")
    
    def _remove_duplicates(self):
        """Удаление дубликатов токенов по адресу контракта"""
        seen_addresses = set()
        unique_tokens = []
        
        for token in self.discovered_tokens:
            if token.contract_address not in seen_addresses:
                seen_addresses.add(token.contract_address)
                unique_tokens.append(token)
        
        self.discovered_tokens = unique_tokens
        logger.info(f"После удаления дубликатов осталось {len(self.discovered_tokens)} токенов")
    
    def _save_evaluation_results(self):
        """Сохранение результатов оценки"""
        if not self.evaluated_tokens:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохранение в JSON
        json_filename = f"evaluation_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump([self._assessment_to_dict(assessment) for assessment in self.evaluated_tokens], 
                     f, indent=2, ensure_ascii=False, default=str)
        
        # Сохранение в CSV
        csv_filename = f"evaluation_results_{timestamp}.csv"
        df = pd.DataFrame([self._assessment_to_dict(assessment) for assessment in self.evaluated_tokens])
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        logger.info(f"Результаты оценки сохранены в {json_filename} и {csv_filename}")
    
    def _assessment_to_dict(self, assessment: TokenAssessment) -> Dict:
        """Преобразование оценки в словарь для сохранения"""
        return {
            'contract_address': assessment.contract_address,
            'name': assessment.name,
            'symbol': assessment.symbol,
            'overall_score': assessment.overall_score,
            'security_score': assessment.security_score,
            'liquidity_score': assessment.liquidity_score,
            'community_score': assessment.community_score,
            'risk_level': assessment.risk_level,
            'recommendation': assessment.recommendation,
            'red_flags': '; '.join(assessment.red_flags) if assessment.red_flags else '',
            'green_flags': '; '.join(assessment.green_flags) if assessment.green_flags else '',
            'assessment_date': assessment.assessment_date
        }
    
    def _update_stats(self):
        """Обновление статистики системы"""
        self.stats['tokens_discovered'] = len(self.discovered_tokens)
        self.stats['tokens_evaluated'] = len(self.evaluated_tokens)
        self.stats['tokens_monitored'] = len(self.monitored_tokens)
        self.stats['last_update'] = datetime.now().isoformat()
        
        # Подсчет токенов по категориям риска
        if self.evaluated_tokens:
            self.stats['scams_detected'] = len([
                t for t in self.evaluated_tokens 
                if t.recommendation == 'SCAM'
            ])
            self.stats['high_risk_tokens'] = len([
                t for t in self.evaluated_tokens 
                if t.risk_level in ['HIGH', 'CRITICAL']
            ])
    
    def get_summary_report(self) -> Dict:
        """Получение сводного отчета по работе системы"""
        return {
            'system_status': 'active',
            'last_update': self.stats['last_update'],
            'statistics': self.stats,
            'risk_distribution': self._get_risk_distribution(),
            'recommendation_distribution': self._get_recommendation_distribution(),
            'top_tokens': self._get_top_tokens(),
            'high_risk_tokens': self._get_high_risk_tokens()
        }
    
    def _get_risk_distribution(self) -> Dict:
        """Распределение токенов по уровням риска"""
        if not self.evaluated_tokens:
            return {}
        
        distribution = {}
        for assessment in self.evaluated_tokens:
            risk_level = assessment.risk_level
            distribution[risk_level] = distribution.get(risk_level, 0) + 1
        
        return distribution
    
    def _get_recommendation_distribution(self) -> Dict:
        """Распределение токенов по рекомендациям"""
        if not self.evaluated_tokens:
            return {}
        
        distribution = {}
        for assessment in self.evaluated_tokens:
            recommendation = assessment.recommendation
            distribution[recommendation] = distribution.get(recommendation, 0) + 1
        
        return distribution
    
    def _get_top_tokens(self, limit: int = 10) -> List[Dict]:
        """Получение топ токенов по общему баллу"""
        if not self.evaluated_tokens:
            return []
        
        sorted_tokens = sorted(
            self.evaluated_tokens, 
            key=lambda x: x.overall_score, 
            reverse=True
        )
        
        return [
            {
                'symbol': t.symbol,
                'name': t.name,
                'overall_score': t.overall_score,
                'risk_level': t.risk_level,
                'recommendation': t.recommendation
            }
            for t in sorted_tokens[:limit]
        ]
    
    def _get_high_risk_tokens(self) -> List[Dict]:
        """Получение токенов с высоким риском"""
        high_risk = [
            t for t in self.evaluated_tokens 
            if t.risk_level in ['HIGH', 'CRITICAL']
        ]
        
        return [
            {
                'symbol': t.symbol,
                'name': t.name,
                'contract_address': t.contract_address,
                'risk_level': t.risk_level,
                'overall_score': t.overall_score,
                'red_flags': t.red_flags or []
            }
            for t in high_risk
        ]
    
    async def stop_monitoring(self):
        """Остановка системы мониторинга"""
        logger.info("Останавливаю систему мониторинга...")
        self.monitor.monitoring_active = False
    
    def export_all_data(self, output_dir: str = "token_evaluation_export"):
        """Экспорт всех данных системы"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Экспорт обнаруженных токенов
        if self.discovered_tokens:
            df_discovered = pd.DataFrame([
                {
                    'name': t.name,
                    'symbol': t.symbol,
                    'contract_address': t.contract_address,
                    'market_cap_usd': t.market_cap_usd,
                    'volume_24h_usd': t.volume_24h_usd,
                    'discovery_method': t.discovery_method
                }
                for t in self.discovered_tokens
            ])
            df_discovered.to_csv(output_path / f"discovered_tokens_{timestamp}.csv", index=False)
        
        # Экспорт результатов оценки
        if self.evaluated_tokens:
            df_evaluated = pd.DataFrame([
                self._assessment_to_dict(t) for t in self.evaluated_tokens
            ])
            df_evaluated.to_csv(output_path / f"evaluated_tokens_{timestamp}.csv", index=False)
        
        # Экспорт отчета
        report = self.get_summary_report()
        with open(output_path / f"summary_report_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Все данные экспортированы в {output_path}")


async def main():
    """Основная функция для тестирования системы"""
    logger.info("Запуск системы оценки ERC-20 токенов")
    
    # Создание системы
    system = TokenEvaluationSystem()
    
    try:
        # Запуск полного цикла оценки
        await system.run_full_evaluation_cycle()
        
        # Получение отчета
        report = system.get_summary_report()
        logger.info("Сводный отчет:")
        logger.info(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        
        # Экспорт данных
        system.export_all_data()
        
        # Остановка мониторинга
        await system.stop_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        await system.stop_monitoring()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await system.stop_monitoring()
        raise


if __name__ == "__main__":
    asyncio.run(main())
