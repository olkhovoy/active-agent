import os
import json
import time
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from web3 import Web3
from eth_abi import decode_abi
import hashlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityMetrics:
    """Метрики безопасности токена"""
    has_verified_source: bool = False
    has_audit_report: bool = False
    has_multisig_wallet: bool = False
    has_timelock: bool = False
    has_blacklist_function: bool = False
    has_mint_function: bool = False
    has_pause_function: bool = False
    owner_privileges: int = 0  # Количество привилегированных функций
    risk_score: float = 0.0

@dataclass
class LiquidityMetrics:
    """Метрики ликвидности токена"""
    total_liquidity_usd: float = 0.0
    liquidity_distribution: Dict[str, float] = None  # Распределение по DEX
    liquidity_concentration: float = 0.0  # Концентрация ликвидности
    slippage_impact: float = 0.0  # Влияние на цену при больших сделках

@dataclass
class CommunityMetrics:
    """Метрики сообщества токена"""
    github_activity: float = 0.0
    social_media_presence: float = 0.0
    community_size: int = 0
    developer_activity: float = 0.0
    documentation_quality: float = 0.0

@dataclass
class TokenAssessment:
    """Комплексная оценка токена"""
    contract_address: str
    name: str
    symbol: str
    overall_score: float = 0.0
    security_score: float = 0.0
    liquidity_score: float = 0.0
    community_score: float = 0.0
    risk_level: str = "UNKNOWN"  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation: str = "REVIEW"  # INVEST, HOLD, AVOID, SCAM
    security_metrics: SecurityMetrics = None
    liquidity_metrics: LiquidityMetrics = None
    community_metrics: CommunityMetrics = None
    red_flags: List[str] = None
    green_flags: List[str] = None
    assessment_date: str = None

class AdvancedTokenEvaluator:
    """Продвинутый агент для оценки ERC-20 токенов"""
    
    def __init__(self):
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.infura_api_key = os.getenv('INFURA_API_KEY')
        
        # Инициализация Web3
        if self.infura_api_key:
            self.w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{self.infura_api_key}'))
        else:
            self.w3 = None
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AdvancedTokenEvaluator/1.0'})
        
        # Загрузка известных скам-паттернов
        self.scam_patterns = self._load_scam_patterns()
        
    def _load_scam_patterns(self) -> Dict:
        """Загрузка известных паттернов скама"""
        return {
            'suspicious_names': [
                'moon', 'safe', 'elon', 'inu', 'doge', 'shib', 'baby', 'mini',
                'rocket', 'moon', 'safe', 'elon', 'inu', 'doge', 'shib'
            ],
            'suspicious_symbols': [
                'MOON', 'SAFE', 'ELON', 'INU', 'DOGE', 'SHIB', 'BABY', 'MINI',
                'ROCKET', 'MOON', 'SAFE', 'ELON', 'INU', 'DOGE', 'SHIB'
            ],
            'high_risk_contracts': [
                '0x0000000000000000000000000000000000000000',  # Zero address
                '0x1111111111111111111111111111111111111111',  # Known scam
            ],
            'suspicious_functions': [
                '0x8450fbbd',  # mint
                '0x8450fbbd',  # pause
                '0x8450fbbd',  # blacklist
            ]
        }
    
    def evaluate_token(self, contract_address: str, token_data: Dict = None) -> TokenAssessment:
        """Основная функция оценки токена"""
        logger.info(f"Начинаю оценку токена {contract_address}")
        
        # Создаем объект оценки
        assessment = TokenAssessment(
            contract_address=contract_address,
            name=token_data.get('name', 'Unknown') if token_data else 'Unknown',
            symbol=token_data.get('symbol', 'UNKNOWN') if token_data else 'UNKNOWN',
            assessment_date=datetime.now().isoformat(),
            red_flags=[],
            green_flags=[],
            security_metrics=SecurityMetrics(),
            liquidity_metrics=LiquidityMetrics(),
            community_metrics=CommunityMetrics()
        )
        
        try:
            # 1. Анализ безопасности контракта
            security_score, security_metrics = self._analyze_security(contract_address)
            assessment.security_score = security_score
            assessment.security_metrics = security_metrics
            
            # 2. Анализ ликвидности
            liquidity_score, liquidity_metrics = self._analyze_liquidity(contract_address, token_data)
            assessment.liquidity_score = liquidity_score
            assessment.liquidity_metrics = liquidity_metrics
            
            # 3. Анализ сообщества
            community_score, community_metrics = self._analyze_community(contract_address, token_data)
            assessment.community_score = community_score
            assessment.community_metrics = community_metrics
            
            # 4. Выявление красных флагов
            red_flags = self._identify_red_flags(contract_address, token_data, security_metrics)
            assessment.red_flags = red_flags
            
            # 5. Выявление зеленых флагов
            green_flags = self._identify_green_flags(contract_address, token_data, security_metrics)
            assessment.green_flags = green_flags
            
            # 6. Расчет общего скора
            assessment.overall_score = self._calculate_overall_score(
                security_score, liquidity_score, community_score, len(red_flags), len(green_flags)
            )
            
            # 7. Определение уровня риска
            assessment.risk_level = self._determine_risk_level(assessment.overall_score, len(red_flags))
            
            # 8. Формирование рекомендации
            assessment.recommendation = self._generate_recommendation(assessment)
            
        except Exception as e:
            logger.error(f"Ошибка при оценке токена {contract_address}: {e}")
            assessment.red_flags.append(f"Ошибка оценки: {str(e)}")
            assessment.overall_score = 0.0
            assessment.risk_level = "CRITICAL"
            assessment.recommendation = "AVOID"
        
        return assessment
    
    def _analyze_security(self, contract_address: str) -> Tuple[float, SecurityMetrics]:
        """Анализ безопасности смарт-контракта"""
        logger.info(f"Анализирую безопасность контракта {contract_address}")
        
        security_metrics = SecurityMetrics()
        security_score = 0.0
        
        try:
            # Получаем ABI контракта
            contract_abi = self._get_contract_abi(contract_address)
            if not contract_abi:
                security_metrics.red_flags.append("Не удалось получить ABI контракта")
                return 0.0, security_metrics
            
            # Анализируем функции контракта
            functions = self._extract_functions_from_abi(contract_abi)
            
            # Проверяем наличие верифицированного исходного кода
            if self._is_contract_verified(contract_address):
                security_metrics.has_verified_source = True
                security_score += 20
                security_metrics.green_flags.append("Контракт верифицирован")
            else:
                security_metrics.red_flags.append("Контракт не верифицирован")
            
            # Проверяем наличие аудита
            if self._has_audit_report(contract_address):
                security_metrics.has_audit_report = True
                security_score += 25
                security_metrics.green_flags.append("Есть отчет об аудите")
            
            # Анализируем функции на предмет рисков
            risk_functions = self._analyze_risk_functions(functions)
            security_metrics.owner_privileges = len(risk_functions)
            
            # Штрафуем за каждую рискованную функцию
            for func in risk_functions:
                if func == 'mint':
                    security_metrics.has_mint_function = True
                    security_score -= 15
                    security_metrics.red_flags.append("Функция mint - риск инфляции")
                elif func == 'pause':
                    security_metrics.has_pause_function = True
                    security_score -= 10
                    security_metrics.red_flags.append("Функция pause - может заблокировать токены")
                elif func == 'blacklist':
                    security_metrics.has_blacklist_function = True
                    security_score -= 20
                    security_metrics.red_flags.append("Функция blacklist - может заблокировать адреса")
            
            # Проверяем на мультисиг
            if self._has_multisig_wallet(contract_address):
                security_metrics.has_multisig_wallet = True
                security_score += 15
                security_metrics.green_flags.append("Используется мультисиг кошелек")
            
            # Проверяем на timelock
            if self._has_timelock(contract_address):
                security_metrics.has_timelock = True
                security_score += 10
                security_metrics.green_flags.append("Используется timelock")
            
            # Нормализуем скор до 0-100
            security_score = max(0, min(100, security_score))
            security_metrics.risk_score = 100 - security_score
            
        except Exception as e:
            logger.error(f"Ошибка при анализе безопасности: {e}")
            security_score = 0.0
        
        return security_score, security_metrics
    
    def _analyze_liquidity(self, contract_address: str, token_data: Dict = None) -> Tuple[float, LiquidityMetrics]:
        """Анализ ликвидности токена"""
        logger.info(f"Анализирую ликвидность токена {contract_address}")
        
        liquidity_metrics = LiquidityMetrics()
        liquidity_score = 0.0
        
        try:
            # Получаем данные о ликвидности через CoinGecko
            if token_data and token_data.get('coingecko_id'):
                liquidity_data = self._get_liquidity_data_coingecko(token_data['coingecko_id'])
                if liquidity_data:
                    liquidity_metrics.total_liquidity_usd = liquidity_data.get('total_liquidity', 0)
                    liquidity_metrics.liquidity_distribution = liquidity_data.get('distribution', {})
                    
                    # Оцениваем качество ликвидности
                    if liquidity_metrics.total_liquidity_usd > 1000000:  # > $1M
                        liquidity_score += 30
                        liquidity_metrics.green_flags.append("Высокая ликвидность")
                    elif liquidity_metrics.total_liquidity_usd > 100000:  # > $100K
                        liquidity_score += 20
                        liquidity_metrics.green_flags.append("Средняя ликвидность")
                    else:
                        liquidity_metrics.red_flags.append("Низкая ликвидность")
            
            # Анализируем распределение ликвидности по DEX
            if liquidity_metrics.liquidity_distribution:
                concentration = self._calculate_liquidity_concentration(liquidity_metrics.liquidity_distribution)
                liquidity_metrics.liquidity_concentration = concentration
                
                if concentration < 0.5:  # Хорошее распределение
                    liquidity_score += 20
                    liquidity_metrics.green_flags.append("Хорошее распределение ликвидности")
                elif concentration > 0.8:  # Высокая концентрация
                    liquidity_score -= 15
                    liquidity_metrics.red_flags.append("Высокая концентрация ликвидности")
            
            # Проверяем влияние на цену при больших сделках
            slippage = self._calculate_slippage_impact(contract_address)
            liquidity_metrics.slippage_impact = slippage
            
            if slippage < 0.05:  # < 5%
                liquidity_score += 20
                liquidity_metrics.green_flags.append("Низкое влияние на цену")
            elif slippage > 0.20:  # > 20%
                liquidity_score -= 20
                liquidity_metrics.red_flags.append("Высокое влияние на цену")
            
            # Нормализуем скор
            liquidity_score = max(0, min(100, liquidity_score))
            
        except Exception as e:
            logger.error(f"Ошибка при анализе ликвидности: {e}")
            liquidity_score = 0.0
        
        return liquidity_score, liquidity_metrics
    
    def _analyze_community(self, contract_address: str, token_data: Dict = None) -> Tuple[float, CommunityMetrics]:
        """Анализ сообщества токена"""
        logger.info(f"Анализирую сообщество токена {contract_address}")
        
        community_metrics = CommunityMetrics()
        community_score = 0.0
        
        try:
            # Анализируем активность в GitHub
            if token_data and token_data.get('github_url'):
                github_activity = self._analyze_github_activity(token_data['github_url'])
                community_metrics.github_activity = github_activity
                
                if github_activity > 0.7:
                    community_score += 25
                    community_metrics.green_flags.append("Высокая активность разработки")
                elif github_activity > 0.3:
                    community_score += 15
                    community_metrics.green_flags.append("Средняя активность разработки")
                else:
                    community_metrics.red_flags.append("Низкая активность разработки")
            
            # Анализируем социальные сети
            social_presence = self._analyze_social_media_presence(contract_address, token_data)
            community_metrics.social_media_presence = social_presence
            
            if social_presence > 0.6:
                community_score += 20
                community_metrics.green_flags.append("Активное присутствие в соцсетях")
            elif social_presence < 0.2:
                community_metrics.red_flags.append("Слабое присутствие в соцсетях")
            
            # Оцениваем качество документации
            doc_quality = self._assess_documentation_quality(contract_address, token_data)
            community_metrics.documentation_quality = doc_quality
            
            if doc_quality > 0.7:
                community_score += 20
                community_metrics.green_flags.append("Качественная документация")
            elif doc_quality < 0.3:
                community_score -= 15
                community_metrics.red_flags.append("Плохая документация")
            
            # Нормализуем скор
            community_score = max(0, min(100, community_score))
            
        except Exception as e:
            logger.error(f"Ошибка при анализе сообщества: {e}")
            community_score = 0.0
        
        return community_score, community_metrics
    
    def _identify_red_flags(self, contract_address: str, token_data: Dict, 
                           security_metrics: SecurityMetrics) -> List[str]:
        """Выявление красных флагов"""
        red_flags = []
        
        # Проверяем подозрительные имена и символы
        if token_data:
            name = token_data.get('name', '').lower()
            symbol = token_data.get('symbol', '').upper()
            
            for pattern in self.scam_patterns['suspicious_names']:
                if pattern in name:
                    red_flags.append(f"Подозрительное имя: содержит '{pattern}'")
            
            for pattern in self.scam_patterns['suspicious_symbols']:
                if pattern in symbol:
                    red_flags.append(f"Подозрительный символ: содержит '{pattern}'")
        
        # Проверяем контракт на известные скам-адреса
        if contract_address.lower() in [addr.lower() for addr in self.scam_patterns['high_risk_contracts']]:
            red_flags.append("Известный скам-контракт")
        
        # Добавляем флаги из анализа безопасности
        if security_metrics:
            if security_metrics.has_mint_function:
                red_flags.append("Функция mint - риск неконтролируемой эмиссии")
            if security_metrics.has_blacklist_function:
                red_flags.append("Функция blacklist - может заблокировать пользователей")
            if security_metrics.owner_privileges > 3:
                red_flags.append(f"Слишком много привилегированных функций: {security_metrics.owner_privileges}")
        
        return red_flags
    
    def _identify_green_flags(self, contract_address: str, token_data: Dict, 
                             security_metrics: SecurityMetrics) -> List[str]:
        """Выявление зеленых флагов"""
        green_flags = []
        
        # Добавляем флаги из анализа безопасности
        if security_metrics:
            if security_metrics.has_verified_source:
                green_flags.append("Верифицированный исходный код")
            if security_metrics.has_audit_report:
                green_flags.append("Прошел аудит безопасности")
            if security_metrics.has_multisig_wallet:
                green_flags.append("Использует мультисиг кошелек")
            if security_metrics.has_timelock:
                green_flags.append("Использует timelock для изменений")
        
        # Проверяем на наличие whitepaper
        if token_data and token_data.get('whitepaper_url'):
            green_flags.append("Есть техническая документация")
        
        # Проверяем на наличие roadmap
        if token_data and token_data.get('roadmap_url'):
            green_flags.append("Есть roadmap развития")
        
        return green_flags
    
    def _calculate_overall_score(self, security_score: float, liquidity_score: float, 
                                community_score: float, red_flags_count: int, 
                                green_flags_count: int) -> float:
        """Расчет общего скора"""
        # Базовый скор - среднее взвешенное
        base_score = (security_score * 0.4 + liquidity_score * 0.3 + community_score * 0.3)
        
        # Штраф за красные флаги
        red_flag_penalty = red_flags_count * 10
        
        # Бонус за зеленые флаги
        green_flag_bonus = green_flags_count * 5
        
        # Финальный скор
        final_score = base_score - red_flag_penalty + green_flag_bonus
        
        return max(0, min(100, final_score))
    
    def _determine_risk_level(self, overall_score: float, red_flags_count: int) -> str:
        """Определение уровня риска"""
        if red_flags_count >= 5 or overall_score < 20:
            return "CRITICAL"
        elif red_flags_count >= 3 or overall_score < 40:
            return "HIGH"
        elif red_flags_count >= 1 or overall_score < 60:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, assessment: TokenAssessment) -> str:
        """Генерация рекомендации"""
        if assessment.risk_level == "CRITICAL" or assessment.overall_score < 20:
            return "AVOID"
        elif assessment.risk_level == "HIGH" or assessment.overall_score < 40:
            return "HOLD"
        elif assessment.overall_score >= 70:
            return "INVEST"
        else:
            return "REVIEW"
    
    # Вспомогательные методы (заглушки для демонстрации)
    def _get_contract_abi(self, contract_address: str) -> Optional[List]:
        """Получение ABI контракта"""
        if not self.etherscan_api_key:
            return None
        
        try:
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': self.etherscan_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    return json.loads(data['result'])
        except Exception as e:
            logger.error(f"Ошибка при получении ABI: {e}")
        
        return None
    
    def _is_contract_verified(self, contract_address: str) -> bool:
        """Проверка верификации контракта"""
        # Заглушка - в реальности нужно проверять через Etherscan API
        return True
    
    def _has_audit_report(self, contract_address: str) -> bool:
        """Проверка наличия аудита"""
        # Заглушка - в реальности нужно проверять через различные источники
        return False
    
    def _has_multisig_wallet(self, contract_address: str) -> bool:
        """Проверка использования мультисиг кошелька"""
        # Заглушка
        return False
    
    def _has_timelock(self, contract_address: str) -> bool:
        """Проверка использования timelock"""
        # Заглушка
        return False
    
    def _extract_functions_from_abi(self, abi: List) -> List[str]:
        """Извлечение функций из ABI"""
        functions = []
        for item in abi:
            if item.get('type') == 'function':
                functions.append(item.get('name', ''))
        return functions
    
    def _analyze_risk_functions(self, functions: List[str]) -> List[str]:
        """Анализ рискованных функций"""
        risk_functions = []
        for func in functions:
            if func in ['mint', 'pause', 'blacklist', 'freeze', 'transferOwnership']:
                risk_functions.append(func)
        return risk_functions
    
    def _get_liquidity_data_coingecko(self, coingecko_id: str) -> Optional[Dict]:
        """Получение данных о ликвидности через CoinGecko"""
        # Заглушка
        return {'total_liquidity': 1000000, 'distribution': {'uniswap': 0.6, 'sushiswap': 0.4}}
    
    def _calculate_liquidity_concentration(self, distribution: Dict[str, float]) -> float:
        """Расчет концентрации ликвидности"""
        if not distribution:
            return 1.0
        
        # Используем индекс Херфиндаля-Хиршмана
        hhi = sum(share ** 2 for share in distribution.values())
        return hhi
    
    def _calculate_slippage_impact(self, contract_address: str) -> float:
        """Расчет влияния на цену при больших сделках"""
        # Заглушка
        return 0.1
    
    def _analyze_github_activity(self, github_url: str) -> float:
        """Анализ активности в GitHub"""
        # Заглушка
        return 0.5
    
    def _analyze_social_media_presence(self, contract_address: str, token_data: Dict) -> float:
        """Анализ присутствия в социальных сетях"""
        # Заглушка
        return 0.4
    
    def _assess_documentation_quality(self, contract_address: str, token_data: Dict) -> float:
        """Оценка качества документации"""
        # Заглушка
        return 0.6

def main():
    """Тестирование продвинутого оценщика токенов"""
    evaluator = AdvancedTokenEvaluator()
    
    # Тестовый токен
    test_token = {
        'name': 'Test Token',
        'symbol': 'TEST',
        'coingecko_id': 'test-token',
        'github_url': 'https://github.com/test/token'
    }
    
    # Оцениваем токен
    assessment = evaluator.evaluate_token(
        '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',  # Uniswap
        test_token
    )
    
    # Выводим результаты
    print(f"Оценка токена: {assessment.name} ({assessment.symbol})")
    print(f"Общий скор: {assessment.overall_score:.1f}/100")
    print(f"Уровень риска: {assessment.risk_level}")
    print(f"Рекомендация: {assessment.recommendation}")
    print(f"Безопасность: {assessment.security_score:.1f}/100")
    print(f"Ликвидность: {assessment.liquidity_score:.1f}/100")
    print(f"Сообщество: {assessment.community_score:.1f}/100")
    
    if assessment.red_flags:
        print("\nКрасные флаги:")
        for flag in assessment.red_flags:
            print(f"  ❌ {flag}")
    
    if assessment.green_flags:
        print("\nЗеленые флаги:")
        for flag in assessment.green_flags:
            print(f"  ✅ {flag}")

if __name__ == "__main__":
    main()
