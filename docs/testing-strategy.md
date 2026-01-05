# Testing Strategy for Vanguard

## Test Database Configuration

### Repository Layer Tests (`@DataJpaTest`)

**Configuration:**
- **Test Database:** H2 (in-memory)
- **Production Database:** PostgreSQL
- **SQL Initialization:** Disabled in tests (`spring.sql.init.mode=never`)

**Why H2 for Tests?**
- Fast: In-memory database, no disk I/O
- Isolated: Each test gets a fresh database
- No setup: No Docker containers needed
- Standard: Industry best practice for JPA testing

**Why Disable data.sql in Tests?**
- Tests create their own test data in `@BeforeEach`
- Avoids dependency on external SQL files
- Allows testing edge cases (empty database, specific states)
- True test isolation: each test starts clean

**Example Test Setup:**
```java
@DataJpaTest
@TestPropertySource(properties = "spring.sql.init.mode=never")
class PartRepositoryTest {

    @BeforeEach
    void setUp() {
        // Create test-specific data
        Part testPart = new Part(...);
        entityManager.persist(testPart);
        entityManager.flush();
    }
}
```

---

## Testing Pyramid

### Layer 1: Repository Tests (Current)
- **Tool:** `@DataJpaTest` + H2
- **What:** Test database queries (JPQL, derived methods)
- **Speed:** Very fast (milliseconds)
- **Coverage:** Data access logic

### Layer 2: Service Tests (Coming Next)
- **Tool:** `@SpringBootTest` (or `@ExtendWith(MockitoExtension.class)`)
- **What:** Test business logic with mocked repositories
- **Speed:** Fast (no database)
- **Coverage:** Business rules, validation

### Layer 3: Integration Tests (Coming Next)
- **Tool:** `@SpringBootTest` + Testcontainers
- **What:** Test full stack with real PostgreSQL + Kafka
- **Speed:** Slower (spins up Docker containers)
- **Coverage:** End-to-end flows

---

## Common Pitfalls Avoided

### ❌ Pitfall 1: Using Production Database for Tests
**Problem:** Tests can corrupt production data, slow, requires setup
**Solution:** Use H2 for repository tests

### ❌ Pitfall 2: Shared Test Data Across Tests
**Problem:** Tests affect each other, hard to debug failures
**Solution:** Each test creates its own data in `@BeforeEach`

### ❌ Pitfall 3: Testing Against Different Databases (Prod vs Test)
**Problem:** H2 SQL dialect differs slightly from PostgreSQL
**Mitigation:**
- Use standard JPQL (not native SQL)
- Run integration tests with Testcontainers + PostgreSQL for critical flows
- Our setup: Repository tests use H2, integration tests will use PostgreSQL

---

## Test Execution

### Run All Tests
```bash
mvn test
```

### Run Specific Test Class
```bash
mvn test -Dtest=PartRepositoryTest
```

### Run Tests with Coverage
```bash
mvn test jacoco:report
# Report: target/site/jacoco/index.html
```

---

## Dependencies

### Test Scope Dependencies (pom.xml)
```xml
<!-- H2 for fast in-memory testing -->
<dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <scope>test</scope>
</dependency>

<!-- Spring Boot Test Starter -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>

<!-- Testcontainers (for integration tests - coming in Phase 2) -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <version>1.19.3</version>
    <scope>test</scope>
</dependency>
```
