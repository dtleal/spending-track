# SpendTrack - AI-Powered Personal Finance Manager

An intelligent spending tracker web application that helps you manage your finances through automated invoice parsing, AI-driven insights, and beautiful data visualizations.

## 🚀 Features

- **AI-Powered Invoice Processing**: Automatically parse and extract data from CSV invoices
- **Smart Categorization**: AI-driven automatic expense categorization
- **Interactive Dashboard**: Beautiful charts and visualizations for spending analysis
- **Advanced Filtering**: Multiple filter options to analyze spending patterns
- **Real-time Insights**: Get AI-generated insights about your spending habits
- **Multi-format Export**: Export your data in various formats for further analysis

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database for structured financial data
- **Elasticsearch**: For advanced search and analytics capabilities
- **FastMCP**: AI integration for intelligent data processing
- **Docker**: Containerization for easy deployment
- **uv**: Fast Python package manager

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI components
- **Recharts**: Beautiful chart visualizations
- **React Query**: Efficient data fetching and caching

### AI Integration
- **FastMCP**: For server/client AI communication
- **OpenAI SDK**: For advanced natural language processing
- **Custom ML Models**: For expense categorization and pattern detection

## 📁 Project Structure

```
spending-track/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── invoices.py
│   │   │   │   ├── expenses.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── ai_insights.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── ai_client.py
│   │   ├── models/
│   │   │   ├── expense.py
│   │   │   ├── invoice.py
│   │   │   └── user.py
│   │   ├── services/
│   │   │   ├── invoice_parser.py
│   │   │   ├── expense_categorizer.py
│   │   │   └── analytics_engine.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   ├── expenses/
│   │   │   ├── analytics/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── charts/
│   │   │   └── filters/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── types/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── invoices/
│   └── fatura-99999999.csv
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Elasticsearch 8+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spending-track.git
cd spending-track
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the application with Docker:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Development Setup

#### Backend
```bash
cd backend
pip install uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Features in Detail

### Invoice Processing
- Supports CSV format (with plans for PDF, Excel)
- Automatic data extraction and validation
- Batch processing capabilities
- Error handling and logging

### Expense Management
- Automatic categorization using AI
- Manual category override
- Tags and labels support
- Recurring expense detection

### Analytics Dashboard
- Monthly/yearly spending trends
- Category-wise breakdown
- Merchant analysis
- Custom date range filtering
- Export to CSV/Excel/PDF

### AI Insights
- Spending pattern analysis
- Budget recommendations
- Anomaly detection
- Predictive analytics for future expenses

## 🔧 Configuration

### Environment Variables

```env
# Backend
DATABASE_URL=postgresql://user:password@localhost/spendtrack
ELASTICSEARCH_URL=http://localhost:9200
OPENAI_API_KEY=your_openai_api_key
FASTMCP_SERVER_URL=http://localhost:8001
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=SpendTrack
```

## 📝 API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/invoices/upload` - Upload invoice file
- `GET /api/expenses` - List expenses with filters
- `GET /api/analytics/summary` - Get spending summary
- `POST /api/ai/insights` - Generate AI insights

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
npm run test:e2e
```

## 🚢 Deployment

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
See detailed deployment instructions in `docs/deployment.md`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Invoice data parsing inspired by financial management best practices
- UI components from shadcn/ui
- Charts powered by Recharts
- AI capabilities powered by OpenAI and FastMCP