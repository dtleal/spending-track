make# SpendTrack - Claude Development Notes

This document contains important information for Claude Code about the SpendTrack project structure, conventions, and development workflows.

## Project Overview

SpendTrack is an AI-powered personal finance manager that automatically processes invoice data, categorizes expenses using AI, and provides intelligent insights through a modern web interface.

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL for structured data
- **Search**: Elasticsearch for analytics
- **Cache**: Redis for session management
- **AI**: OpenAI SDK for expense categorization and insights
- **Package Manager**: uv for fast dependency management

### Frontend (Next.js)
- **Framework**: Next.js 14 with TypeScript
- **UI**: Tailwind CSS + shadcn/ui components
- **Charts**: Recharts for data visualization
- **State**: Zustand for client state
- **Data Fetching**: React Query (TanStack Query)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database Migrations**: Alembic
- **Process Management**: Make-based workflow

## Project Structure

```
spending-track/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, security, AI client
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic (invoice parser, categorizer)
│   │   └── db/             # Database configuration
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js 14 app router
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities, API client, stores
│   │   └── types/         # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── invoices/              # Invoice files for processing
├── docker-compose.yml     # Main services configuration
├── docker-compose.dev.yml # Development overrides
├── Makefile              # Development commands
└── README.md
```

## Development Workflow

### Common Commands
- `make setup` - First-time project setup
- `make build` - Build all containers
- `make start` - Start all services
- `make dev` - Start development environment
- `make logs` - View service logs
- `make lint` - Run code linting (ruff + pylint)
- `make test` - Run all tests
- `make migrate` - Run database migrations

### Code Quality Standards
- **Python**: Use ruff for linting, black for formatting, pylint for additional checks
- **TypeScript**: ESLint + Prettier via Next.js
- **Line Length**: 88 characters
- **Import Sorting**: Handled by ruff/isort

### Database Operations
- **Create Migration**: `make makemigrations msg="description"`
- **Run Migrations**: `make migrate`
- **Database Shell**: `make shell-db`

### Testing
- **Backend**: pytest with asyncio support
- **Frontend**: Jest + React Testing Library
- **Run Tests**: `make test` or `make test-backend`/`make test-frontend`

## Key Features Implementation

### 1. Invoice Processing
- **Location**: `backend/app/services/invoice_parser.py`
- **Format**: CSV with columns: data, lançamento, valor
- **Process**: Upload → Parse → Validate → Store → AI Categorize

### 2. AI Integration
- **Location**: `backend/app/core/ai_client.py`
- **Provider**: OpenAI GPT-4o-mini
- **Features**: Expense categorization, spending analysis, predictions, chat assistant
- **Configuration**: Set `OPENAI_API_KEY` in backend/.env

### 3. Expense Categories
```python
FOOD, TRANSPORT, SHOPPING, HEALTH, ENTERTAINMENT, 
UTILITIES, EDUCATION, OTHER
```

### 4. Analytics Engine
- **Location**: `backend/app/services/analytics_engine.py`
- **Features**: Spending summaries, trends, unusual spending detection, budget recommendations

## Environment Configuration

### Backend (.env)
```bash
DATABASE_URL=postgresql://spendtrack:spendtrack123@db:5432/spendtrack
ELASTICSEARCH_URL=http://elasticsearch:9200
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Required for AI features
DEBUG=True
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=SpendTrack
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Invoices
- `POST /api/invoices/upload` - Upload CSV invoice
- `GET /api/invoices/` - List user invoices
- `GET /api/invoices/{id}` - Get invoice details

### Expenses  
- `GET /api/expenses/` - List expenses with filters
- `POST /api/expenses/` - Create expense manually
- `PATCH /api/expenses/{id}` - Update expense
- `POST /api/expenses/{id}/categorize` - Re-run AI categorization

### Analytics
- `GET /api/analytics/summary` - Spending summary
- `GET /api/analytics/trends/monthly` - Monthly trends
- `GET /api/analytics/budget/recommendations` - Budget suggestions

### AI Insights
- `POST /api/ai/analyze` - Analyze spending patterns
- `POST /api/ai/predict` - Predict future expenses
- `POST /api/ai/chat` - Chat with AI assistant

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running (`make logs-db`)
2. **AI Features Not Working**: Check `OPENAI_API_KEY` in backend/.env
3. **Frontend Build Issues**: Clear node_modules and rebuild
4. **Invoice Processing Fails**: Check CSV format (data, lançamento, valor columns)

### Useful Debug Commands
```bash
make logs-backend        # Backend logs
make logs-frontend       # Frontend logs  
make shell-backend       # Backend container shell
make health             # Service health check
make seed-data          # Test invoice processing
```

## Performance Considerations

### Backend
- Uses connection pooling for PostgreSQL
- Redis for caching frequently accessed data
- Elasticsearch for complex analytics queries
- Background tasks for invoice processing

### Frontend
- React Query for efficient data fetching and caching
- Code splitting with Next.js
- Optimized bundle with tree shaking
- Responsive design for mobile/desktop

## Security

### Backend
- JWT token authentication
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM

### Frontend
- Client-side token storage (localStorage)
- API request authentication
- XSS protection via React
- Environment variable protection

## Extension Points

### Adding New Expense Categories
1. Update `ExpenseCategory` enum in `backend/app/models/expense.py`
2. Update categorization rules in `backend/app/services/expense_categorizer.py`
3. Update frontend types in `frontend/src/types/index.ts`

### Adding New AI Features
1. Extend `AIClient` in `backend/app/core/ai_client.py`
2. Create new API endpoints in `backend/app/api/endpoints/ai_insights.py`
3. Add frontend integration in `frontend/src/lib/api.ts`

### Adding New Chart Types
1. Create component in `frontend/src/components/charts/`
2. Use Recharts library for consistency
3. Follow existing patterns for data formatting

## Deployment Notes

### Production Considerations
- Set strong `SECRET_KEY` in production
- Use production-grade database (managed PostgreSQL)
- Configure proper CORS origins
- Set up SSL/TLS termination
- Use Redis for session storage in multi-instance deployments
- Monitor OpenAI API usage and costs

### Environment Variables for Production
- `DEBUG=False`
- Strong `SECRET_KEY`
- Production database URLs
- Appropriate `CORS_ORIGINS`
- Real `OPENAI_API_KEY`

## Testing Strategy

### Backend Tests
- Unit tests for services and models
- Integration tests for API endpoints
- Mock external dependencies (OpenAI API)
- Database tests with test fixtures

### Frontend Tests
- Component unit tests
- Integration tests for user flows
- Mock API responses
- Accessibility testing

## Monitoring

### Health Checks
- `/health` endpoint for backend status
- Database connectivity checks
- External service dependency checks
- Custom health check via `make health`

### Logging
- Structured logging in backend
- Request/response logging
- Error tracking and reporting
- Performance metrics collection

---

*Last updated: 2025-01-27*
*This document should be updated when making significant architectural changes.*