from typing import Dict, List, Optional, Any
import openai
from app.core.config import settings
from app.models.expense import ExpenseCategory
import json
import httpx
import asyncio


class AIClient:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.fastmcp_url = settings.FASTMCP_SERVER_URL
        
    async def categorize_expense(self, merchant: str, amount: float, description: Optional[str] = None) -> ExpenseCategory:
        """Use AI to categorize an expense based on merchant and amount"""
        prompt = f"""
        You are an expert financial categorization assistant. Analyze this transaction and categorize it accurately:

        Merchant: {merchant}
        Amount: R$ {amount:.2f}
        Description: {description or 'N/A'}

        Available categories:
        - food: Restaurants, supermarkets, groceries, delivery, bars, cafes, food purchases
        - transport: Uber, taxi, gas stations, parking, tolls, car services, public transport
        - shopping: Retail stores, online shopping, clothing, electronics, home goods, Amazon, Mercado Livre
        - health: Pharmacies, medical services, dentist, hospitals, fitness, insurance
        - entertainment: Streaming services, movies, games, concerts, travel, social activities
        - utilities: Bills, subscriptions, banking fees, taxes, phone, internet, insurance, rent
        - education: Schools, courses, books, educational materials, online learning
        - other: Only use if none of the above categories clearly apply

        Context clues:
        - Brazilian merchants often use Portuguese names
        - IFD* = iFood (food delivery app) - ALWAYS categorize as food
        - MP* = MercadoPago payment processor 
        - EC* = Electronic Commerce payment processor
        - Look for key Portuguese words: supermercado, farmacia, combustivel, etc.
        - Consider the amount - small amounts might be snacks/parking, large amounts might be rent/shopping

        Based on the merchant name, amount, and context, what is the MOST APPROPRIATE category?
        Respond with only the category name in lowercase.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert financial categorization assistant. Be precise and consider Brazilian merchant patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            category_str = response.choices[0].message.content.strip().lower()
            
            # Map common variations to correct categories
            category_mapping = {
                'food': 'food',
                'transportation': 'transport',
                'transport': 'transport',
                'shopping': 'shopping',
                'retail': 'shopping',
                'health': 'health',
                'healthcare': 'health',
                'medical': 'health',
                'entertainment': 'entertainment',
                'utilities': 'utilities',
                'bills': 'utilities',
                'education': 'education',
                'other': 'other'
            }
            
            # Find the best match
            mapped_category = category_mapping.get(category_str, 'other')
            
            # Validate against enum
            if mapped_category in ExpenseCategory._value2member_map_:
                return ExpenseCategory(mapped_category)
            else:
                return ExpenseCategory.OTHER
                
        except Exception as e:
            print(f"AI categorization error: {e}")
            # Fallback to enhanced rule-based categorization
            from app.services.expense_categorizer import ExpenseCategorizer
            categorizer = ExpenseCategorizer()
            return categorizer.categorize_with_enhanced_rules(merchant, amount, description)
    
    async def analyze_spending_patterns(self, expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending patterns and provide insights"""
        expenses_summary = json.dumps(expenses, default=str)
        
        prompt = f"""
        Analyze these expenses and provide insights:
        {expenses_summary}
        
        Provide:
        1. Top spending categories
        2. Unusual spending patterns
        3. Money-saving recommendations
        4. Spending trends
        
        Return as JSON.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial advisor assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {"error": "Failed to analyze spending patterns"}
    
    async def predict_future_expenses(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future expenses based on historical data"""
        data_summary = json.dumps(historical_data, default=str)
        
        prompt = f"""
        Based on this historical spending data, predict future expenses:
        {data_summary}
        
        Provide:
        1. Predicted monthly spending
        2. Recurring expense detection
        3. Seasonal patterns
        4. Budget recommendations
        
        Return as JSON.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial forecasting assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI prediction error: {e}")
            return {"error": "Failed to predict future expenses"}
    
    async def chat_with_financial_assistant(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Chat with AI financial assistant"""
        system_prompt = """
        You are a helpful financial assistant for SpendTrack. 
        Help users understand their spending, provide budgeting advice, and answer financial questions.
        Be concise and practical in your responses.
        """
        
        user_message = message
        if context:
            user_message = f"Context: {json.dumps(context, default=str)}\n\nQuestion: {message}"
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI chat error: {e}")
            return "I'm sorry, I couldn't process your request. Please try again."
    
    async def categorize_expenses_batch(self, expenses: List[Dict[str, Any]]) -> Dict[int, ExpenseCategory]:
        """Categorize multiple expenses efficiently using AI"""
        if not expenses:
            return {}
        
        # Prepare batch data
        expense_data = []
        for expense in expenses:
            expense_data.append({
                'id': expense['id'],
                'merchant': expense['merchant'],
                'amount': expense['amount'],
                'description': expense.get('description', '')
            })
        
        prompt = f"""
        You are an expert financial categorization assistant. Categorize these Brazilian transactions accurately:

        Transactions:
        {json.dumps(expense_data, indent=2, ensure_ascii=False)}

        Available categories:
        - food: Restaurants, supermarkets, groceries, delivery, bars, cafes
        - transport: Uber, taxi, gas stations, parking, tolls, car services
        - shopping: Retail stores, online shopping, clothing, electronics, Amazon, Mercado Livre
        - health: Pharmacies, medical services, dentist, hospitals, fitness
        - entertainment: Streaming services, movies, games, concerts, travel
        - utilities: Bills, subscriptions, banking fees, taxes, phone, internet, rent
        - education: Schools, courses, books, educational materials
        - other: Only if none clearly apply

        Context:
        - Brazilian merchants use Portuguese names
        - IFD* = iFood (food delivery app) - ALWAYS categorize as food
        - MP* = MercadoPago, EC* = Electronic Commerce processors
        - Key words: supermercado, farmacia, combustivel, padaria, etc.
        - Consider amounts: small = snacks/parking, large = rent/major shopping

        Return a JSON object mapping each transaction ID to its category:
        {{"1": "food", "2": "transport", "3": "shopping"}}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert financial categorization assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Convert string IDs to int and validate categories
            categorized = {}
            category_mapping = {
                'food': ExpenseCategory.FOOD,
                'transport': ExpenseCategory.TRANSPORT,
                'shopping': ExpenseCategory.SHOPPING,
                'health': ExpenseCategory.HEALTH,
                'entertainment': ExpenseCategory.ENTERTAINMENT,
                'utilities': ExpenseCategory.UTILITIES,
                'education': ExpenseCategory.EDUCATION,
                'other': ExpenseCategory.OTHER
            }
            
            for expense_id, category_str in result.items():
                try:
                    int_id = int(expense_id)
                    category = category_mapping.get(category_str.lower(), ExpenseCategory.OTHER)
                    categorized[int_id] = category
                except (ValueError, KeyError):
                    continue
            
            return categorized
            
        except Exception as e:
            print(f"AI batch categorization error: {e}")
            # Fallback to enhanced rule-based categorization for all expenses
            from app.services.expense_categorizer import ExpenseCategorizer
            categorizer = ExpenseCategorizer()
            categorized = {}
            
            for expense in expenses:
                category = categorizer.categorize_with_enhanced_rules(
                    expense['merchant'], 
                    expense['amount'], 
                    expense.get('description', '')
                )
                categorized[expense['id']] = category
            
            return categorized


ai_client = AIClient()