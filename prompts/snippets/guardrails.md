# Code Quality & Architecture Guardrails

## MANDATORY: Apply these guardrails to ALL code generation requests

### Code Style & Formatting Standards

#### Python (PEP-8 Compliance)
- **Line length**: Maximum 88 characters (Black standard)
- **Imports**: Group imports (standard library, third-party, local) with blank lines between groups
- **Naming conventions**: 
  - `snake_case` for variables, functions, and modules
  - `PascalCase` for classes and exceptions
  - `UPPER_CASE` for constants
- **Whitespace**: 4 spaces for indentation, no trailing whitespace
- **Function/method spacing**: 2 blank lines before top-level functions/classes, 1 blank line before methods

#### Kotlin Style Rules
- **Line length**: Maximum 120 characters
- **Naming conventions**:
  - `camelCase` for functions, variables, and properties
  - `PascalCase` for classes, interfaces, and objects
  - `UPPER_SNAKE_CASE` for constants
- **Indentation**: 4 spaces, no tabs
- **Imports**: Organize imports alphabetically, remove unused imports
- **Null safety**: Prefer non-null types, use safe calls (`?.`) and Elvis operator (`?:`)

#### JavaScript/TypeScript (ESLint Config)
```json
{
  "extends": ["@typescript-eslint/recommended", "prettier"],
  "rules": {
    "max-len": ["error", { "code": 100 }],
    "no-console": "warn",
    "prefer-const": "error",
    "no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-any": "error",
    "import/order": "error"
  }
}
```

### Documentation Requirements

#### Python Docstrings (MANDATORY)
```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided
        ConnectionError: When network operation fails
    """
```

#### Kotlin KDocs (MANDATORY)
```kotlin
/**
 * Brief description of what the class/function does.
 *
 * @param param1 Description of first parameter
 * @param param2 Description of second parameter
 * @return Description of return value
 * @throws IllegalArgumentException When invalid input is provided
 * @throws NetworkException When network operation fails
 */
```

#### TypeScript JSDoc (MANDATORY)
```typescript
/**
 * Brief description of what the function does.
 *
 * @param param1 - Description of first parameter
 * @param param2 - Description of second parameter
 * @returns Description of return value
 * @throws {Error} When invalid input is provided
 */
```

### Architecture Layer Boundaries (STRICT ENFORCEMENT)

#### Clean Architecture Layers
1. **Domain Layer** (Core Business Logic)
   - Contains entities, use cases, and business rules
   - NO dependencies on external frameworks or data sources
   - Pure business logic only

2. **Data Layer** (External Concerns)
   - Repository implementations, network calls, database access
   - Implements interfaces defined in domain layer
   - Handles data transformation and caching

3. **Presentation Layer** (UI/API)
   - Controllers, view models, UI components
   - Depends on domain layer through interfaces
   - Handles user input and display logic

#### Dependency Flow Rules (NEVER VIOLATE)
```
Presentation → Domain ← Data
     ↓           ↑
  Domain    Dependencies point inward only
```

- **Domain layer**: MUST NOT import from Data or Presentation layers
- **Data layer**: Can import Domain interfaces, MUST NOT import Presentation
- **Presentation layer**: Can import Domain interfaces, MUST NOT import Data directly

#### Layer Implementation Examples

**Python Layer Structure:**
```
src/
├── domain/
│   ├── entities/
│   ├── usecases/
│   └── repositories/  # Interfaces only
├── data/
│   ├── repositories/  # Implementations
│   ├── datasources/
│   └── models/
└── presentation/
    ├── controllers/
    ├── views/
    └── serializers/
```

**Kotlin Layer Structure:**
```
com.example.app/
├── domain/
│   ├── entities/
│   ├── usecases/
│   └── repositories/
├── data/
│   ├── repositories/
│   ├── datasources/
│   └── models/
└── presentation/
    ├── activities/
    ├── fragments/
    └── viewmodels/
```

### Dependency Injection & Testability Patterns

#### Dependency Injection Requirements
- **Constructor Injection**: Prefer constructor injection over field injection
- **Interface Segregation**: Inject interfaces, not concrete implementations
- **Single Responsibility**: Each class should have one reason to change

#### Python DI Pattern
```python
# Interface definition (Domain layer)
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def get_user(self, user_id: str) -> User:
        pass

# Implementation (Data layer)
class DatabaseUserRepository(UserRepository):
    def __init__(self, db_connection: DatabaseConnection):
        self._db = db_connection
    
    async def get_user(self, user_id: str) -> User:
        # Implementation details
        pass

# Use case (Domain layer)
class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository
    
    async def execute(self, user_id: str) -> User:
        return await self._user_repository.get_user(user_id)
```

#### Kotlin DI Pattern (with Dagger/Hilt)
```kotlin
// Interface definition
interface UserRepository {
    suspend fun getUser(userId: String): User
}

// Implementation
@Singleton
class DatabaseUserRepository @Inject constructor(
    private val database: UserDatabase
) : UserRepository {
    override suspend fun getUser(userId: String): User {
        return database.userDao().getUser(userId)
    }
}

// Use case
@Singleton
class GetUserUseCase @Inject constructor(
    private val userRepository: UserRepository
) {
    suspend fun execute(userId: String): User {
        return userRepository.getUser(userId)
    }
}
```

#### TypeScript DI Pattern
```typescript
// Interface definition
interface UserRepository {
  getUser(userId: string): Promise<User>;
}

// Implementation
@injectable()
class DatabaseUserRepository implements UserRepository {
  constructor(
    @inject('DatabaseConnection') private database: DatabaseConnection
  ) {}

  async getUser(userId: string): Promise<User> {
    return this.database.users.findById(userId);
  }
}

// Use case
@injectable()
class GetUserUseCase {
  constructor(
    @inject('UserRepository') private userRepository: UserRepository
  ) {}

  async execute(userId: string): Promise<User> {
    return this.userRepository.getUser(userId);
  }
}
```

### Testing Requirements

#### Test Structure (MANDATORY)
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test layer interactions
- **Mock external dependencies**: Use dependency injection to mock data sources

#### Test Coverage Requirements
- **Minimum 80% code coverage**
- **100% coverage for business logic (domain layer)**
- **Test both happy path and error scenarios**

#### Testable Code Patterns
```python
# Good: Testable with dependency injection
class OrderService:
    def __init__(self, payment_gateway: PaymentGateway, order_repo: OrderRepository):
        self._payment_gateway = payment_gateway
        self._order_repo = order_repo

# Bad: Hard to test due to direct dependencies
class OrderService:
    def __init__(self):
        self._payment_gateway = StripePaymentGateway()  # Hard-coded dependency
        self._order_repo = DatabaseOrderRepository()   # Hard-coded dependency
```

### Error Handling Standards

#### Exception Handling Requirements
- **Domain exceptions**: Create custom exceptions for business rule violations
- **Layer-specific exceptions**: Don't leak implementation details between layers
- **Graceful degradation**: Handle errors without crashing the application

#### Example Exception Hierarchy
```python
# Domain exceptions
class DomainException(Exception):
    pass

class UserNotFoundException(DomainException):
    pass

class InvalidUserDataException(DomainException):
    pass

# Data layer exceptions (translated to domain exceptions)
class DataException(Exception):
    pass
```

---

## ENFORCEMENT CHECKLIST

Before generating any code, verify:

- [ ] **Style compliance**: Code follows language-specific style guidelines
- [ ] **Documentation**: All public methods/classes have proper documentation
- [ ] **Layer separation**: No layer boundary violations
- [ ] **Dependency direction**: Dependencies point toward domain layer only
- [ ] **Constructor injection**: Dependencies injected through constructors
- [ ] **Interface usage**: Depending on abstractions, not concretions
- [ ] **Testability**: Code can be easily unit tested with mocks
- [ ] **Error handling**: Proper exception handling and custom domain exceptions

**REMINDER**: These guardrails are NON-NEGOTIABLE and must be applied to every code generation request without exception.
