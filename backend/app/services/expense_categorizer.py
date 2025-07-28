from typing import Dict, List, Optional
from app.models.expense import ExpenseCategory
import re


class ExpenseCategorizer:
    def __init__(self):
        # Merchant patterns for rule-based categorization
        self.category_patterns = {
            ExpenseCategory.FOOD: [
                r'supermercado|mercado|mercearia',
                r'padaria|bakery',
                r'restaurante|restaurant|rest\b',
                r'lanchonete|lanchon|lanch',
                r'cafe|coffee',
                r'açougue|meat',
                r'hortifruti|frutas',
                r'delivery|ifood|uber\s*eats|rappi',
                r'ifd\*?|ifd\s',  # iFood transactions (IFD* prefix)
                r'pizzaria|pizza',
                r'bar\b|pub\b',
                r'confeitaria|confeit',
                r'donalds|burger|king',
                r'sushi|japanese|izakaya',
                r'churrascaria|bbq',
                r'alimenta[çc][aã]o|alimentos|food',
                r'confianca',  # Supermercado Confianca
                r'real\s*alimentos',
                r'napopi|pizzas',
                r'berton.*martini',
                r'fogaca\s*paes',
                r'nutrisavour'
            ],
            ExpenseCategory.TRANSPORT: [
                r'uber(?!\s*eats)|99|cabify|taxi',
                r'combustivel|combustiveis|posto|gas\s*station|gasolina|alcool|diesel',
                r'estacionamento|parking|park\b',
                r'pedagio|toll',
                r'onibus|bus|metro|subway|trem|train',
                r'aluguel\s*carro|rent.*car|localiza|movida|unidas',
                r'mecanica|oficina|auto\s*center|pneu|tire',
                r'multa|detran|dmv',
                r'seguro\s*auto|car\s*insurance',
                r'sorocaba.*combustiveis',  # Combustiveis Sorocaba
                r'platamo.*posto',
                r'rrm\s*estacionamentos',
                r'pronto\s*park',
                r'jumbo\s*estacionamento',
                r'fabio\s*araujo',  # Ride service driver
                r'david\s*henrique\s*carr'  # Ride service driver
            ],
            ExpenseCategory.SHOPPING: [
                r'amazon|mercado\s*livre|mercado\s*pago|shopee|aliexpress',
                r'loja|store|shop(?!ping)',
                r'roupas|clothes|vestuar[iy]o|fashion',
                r'calcados|sapato|shoe|tenis',
                r'eletro|electronic|tech|computer',
                r'moveis|furniture|decora[çc][aã]o',
                r'livrar[iy]a|books|papelaria',
                r'brinquedo|toys',
                r'cosmeticos|perfum|beauty',
                r'joias|jewelry|relogio|watch',
                r'shopping(?!\s*cart)',
                r'magazine|casas\s*bahia|ponto\s*frio|extra(?!\s)|carrefour',
                r'leroy|materiais|material\s*construcao',
                r'riachuelo|renner|c&a|zara|h&m',
                r'armarinhos',  # Armarinhos Fernando
                r'bazar',  # Bazar Ana PA
                r'casa\s*mendes',
                r'materiais\s*jp',
                r'minuto\s*pa',
                r'melimais',
                r'ebazar',
                r'ranacomerci',
                r'rifanecome'
            ],
            ExpenseCategory.HEALTH: [
                r'farmacia|pharmacy|drogaria|drogasil|droga\s*raia|pague\s*menos',
                r'medico|doctor|clinica|clinic|hospital',
                r'dentista|dental|odonto',
                r'exame|exam|laboratorio|lab',
                r'plano\s*saude|health\s*insurance|unimed|amil|sulamerica',
                r'psico|terapia|therapy|therapist',
                r'nutri|diet',
                r'fisio|physio',
                r'academia|gym|fitness|personal',
                r'yoga|pilates|crossfit'
            ],
            ExpenseCategory.ENTERTAINMENT: [
                r'cinema|movie|filme',
                r'teatro|theater|show|concert',
                r'spotify|netflix|amazon\s*prime|disney|hbo|paramount|streaming',
                r'game|gaming|playstation|xbox|nintendo|steam',
                r'livro|book(?!ing)|kindle',
                r'clube|club(?!\s*card)',
                r'festa|party|evento|event',
                r'viagem|travel|hotel|hostel|airbnb|booking',
                r'turismo|tourism|passeio|tour',
                r'paramount\+?|paramountplus',  # Paramount+ streaming
                r'sesc',  # SESC (social/cultural center)
                r'confraria',  # Confraria San Ferrer (dining/social)
            ],
            ExpenseCategory.UTILITIES: [
                r'luz|energia|eletric|cpfl|enel|light',
                r'agua|water|sabesp|saneamento',
                r'gas(?!\s*station)|comgas',
                r'internet|vivo|claro|tim|oi|net|telefone|phone|celular|mobile',
                r'aluguel(?!\s*carro)|rent(?!.*car)|condominio|iptu',
                r'seguro(?!\s*auto)|insurance(?!.*car)',
                r'banco|bank|tarifa|fee',
                r'cartao|card|anuidade',
                r'imposto|tax|governo|government',
                r'claude\.ai|claude\s*subscription',  # Claude AI subscription
                r'google\s*one',  # Google One storage
                r'apple\.com|apple\s*bill',  # Apple services
                r'contabilizei',  # Contabilizei accounting service
                r'mag\s*servicos',  # Service company
                r'iof\s*compra',  # IOF tax
            ],
            ExpenseCategory.EDUCATION: [
                r'escola|school|colegio|faculdade|university|universidade',
                r'curso|course|aula|class|ensino',
                r'livro\s*didatico|textbook|apostila',
                r'material\s*escolar|school\s*supplies',
                r'mensalidade|tuition',
                r'udemy|coursera|alura|edx',
                r'idioma|language|ingles|english'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self.category_patterns.items()
        }
    
    def categorize_by_rules(self, merchant: str, amount: float) -> ExpenseCategory:
        """Categorize expense using rule-based approach"""
        merchant_lower = merchant.lower()
        
        # Check each category's patterns
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(merchant_lower):
                    return category
        
        # Special cases based on amount
        if amount > 1000:
            # Large amounts might be rent, tuition, etc.
            if any(word in merchant_lower for word in ['imovel', 'aluguel', 'rent']):
                return ExpenseCategory.UTILITIES
            elif any(word in merchant_lower for word in ['escola', 'faculdade', 'university']):
                return ExpenseCategory.EDUCATION
        
        return ExpenseCategory.OTHER
    
    def get_category_suggestions(self, merchant: str) -> List[ExpenseCategory]:
        """Get multiple category suggestions for a merchant"""
        suggestions = []
        merchant_lower = merchant.lower()
        
        # Check each category's patterns and score matches
        for category, patterns in self.compiled_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.search(merchant_lower))
            if matches > 0:
                suggestions.append((category, matches))
        
        # Sort by number of matches
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 3 suggestions
        return [cat for cat, _ in suggestions[:3]]
    
    def analyze_merchant_keywords(self, merchant: str) -> Dict[str, List[str]]:
        """Extract keywords from merchant name for better categorization"""
        # Common words to ignore
        stop_words = {'de', 'da', 'do', 'e', 'com', 'ltda', 'sa', 'me', 'eireli', 'ltd', 'inc', 'corp'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', merchant.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        # Extract numbers (might be store codes, dates, etc.)
        numbers = re.findall(r'\b\d+\b', merchant)
        
        # Extract special patterns
        patterns = {
            'installment': re.findall(r'\b\d+/\d+\b', merchant),
            'has_asterisk': '*' in merchant,
            'has_dash': '-' in merchant,
            'all_caps': merchant.isupper(),
        }
        
        return {
            'keywords': keywords,
            'numbers': numbers,
            'patterns': patterns
        }
    
    def categorize_with_enhanced_rules(self, merchant: str, amount: float, description: Optional[str] = None) -> ExpenseCategory:
        """Enhanced rule-based categorization with better pattern matching"""
        merchant_lower = merchant.lower()
        description_lower = (description or '').lower()
        combined_text = f"{merchant_lower} {description_lower}".strip()
        
        # First try standard rules
        category = self.categorize_by_rules(merchant, amount)
        if category != ExpenseCategory.OTHER:
            return category
        
        # Enhanced rules for common Brazilian merchants and patterns
        enhanced_patterns = {
            ExpenseCategory.UTILITIES: [
                r'subscription|assinatura',
                r'taxa|fee|tarifa',
                r'conta|bill',
                r'pagamento|payment',
                r'mensalidade|monthly',
                r'anuidade|annual',
                r'\.ai|\.com|digital',
                r'servicos|services',
                r'tecnologia|technology',
                r'software|app',
                r'cloud|storage'
            ],
            ExpenseCategory.SHOPPING: [
                r'loja|store',
                r'comercio|commerce',
                r'varejo|retail',
                r'produtos|products',
                r'vendas|sales',
                r'atacado|wholesale',
                r'importacao|import',
                r'distribuidora|distributor',
                r'representacoes|representatives'
            ],
            ExpenseCategory.TRANSPORT: [
                r'transporte|transport',
                r'viagem|travel|trip',
                r'carro|car|auto',
                r'moto|motorcycle',
                r'bike|bicicleta',
                r'logistica|logistics',
                r'entrega|delivery'
            ],
            ExpenseCategory.FOOD: [
                r'alimento|food',
                r'bebida|drink|beverage',
                r'gourmet|delicatessen',
                r'culinaria|culinary',
                r'gastronomia|gastronomy',
                r'sabor|flavor|taste',
                r'kitchen|cozinha'
            ],
            ExpenseCategory.HEALTH: [
                r'saude|health|medical',
                r'clinica|clinic',
                r'laboratorio|laboratory',
                r'medicina|medicine',
                r'terapia|therapy',
                r'bem.estar|wellness',
                r'cuidados|care'
            ],
            ExpenseCategory.ENTERTAINMENT: [
                r'entretenimento|entertainment',
                r'diversao|fun',
                r'lazer|leisure',
                r'cultura|culture',
                r'arte|art',
                r'musica|music',
                r'video|filme|movie',
                r'show|concert|evento',
                r'club|clube',
                r'streaming|media'
            ]
        }
        
        # Check enhanced patterns
        for category_enum, patterns in enhanced_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return category_enum
        
        # Amount-based heuristics for remaining cases
        if amount < 10:
            # Very small amounts - likely snacks, parking, or small purchases
            if any(word in combined_text for word in ['ec', 'mp', 'ifd', 'dl']):
                return ExpenseCategory.FOOD  # Often food purchases via payment processors
            return ExpenseCategory.TRANSPORT  # Parking, tolls, etc.
        elif amount > 500:
            # Large amounts - likely utilities, rent, or major shopping
            if any(word in combined_text for word in ['pagamento', 'taxa', 'conta', 'servico']):
                return ExpenseCategory.UTILITIES
            return ExpenseCategory.SHOPPING
        elif 50 <= amount <= 200:
            # Medium amounts - could be various categories, lean towards shopping
            return ExpenseCategory.SHOPPING
        
        # Default fallback - try to guess based on merchant structure
        if any(char in merchant_lower for char in ['.', '@', 'www']):
            return ExpenseCategory.UTILITIES  # Digital services
        elif merchant_lower.isupper() and len(merchant_lower.split()) == 1:
            return ExpenseCategory.SHOPPING  # Often store codes
        elif any(word in merchant_lower for word in ['ltda', 'me', 'eireli', 'sa']):
            return ExpenseCategory.SHOPPING  # Company suffixes
        
        return ExpenseCategory.OTHER