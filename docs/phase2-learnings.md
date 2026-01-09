# Phase 2: Service Layer - Learnings

## Kafka JSON Deserialization Configuration

### Problem Encountered
`MessageConversionException` when consuming JSON events from Python simulator in Spring Boot.

### Root Causes
1. **Configuration Conflict**: Both `application.yml` and Java config defining deserializer settings
2. **Type Ambiguity**: `Map<String, Object>` requires explicit type configuration
3. **Cross-Language Serialization**: Python sends ISO timestamp strings, Java needed proper Jackson setup

### Solution
Created dedicated `KafkaConfig.java` with explicit deserializer configuration:
```java
config.put(JsonDeserializer.TRUSTED_PACKAGES, "*");
config.put(JsonDeserializer.VALUE_DEFAULT_TYPE, "java.util.Map");
config.put(JsonDeserializer.USE_TYPE_INFO_HEADERS, false);
```

Simplified `application.yml` to only contain basic consumer settings.

### Why This Works
- **Separation of Concerns**: YAML for simple config, Java for complex deserialization
- **Explicit Type Mapping**: Jackson knows to create `Map<String, Object>`
- **Cross-Platform Compatibility**: No Spring-specific type headers required
- **Flexibility**: Can handle any JSON structure from Python

### Best Practices Applied
✅ Use dedicated `@Configuration` class for complex Kafka setup
✅ Keep YAML configuration minimal and focused
✅ Use `Map<String, Object>` for flexible JSON deserialization
✅ Set `TRUSTED_PACKAGES = "*"` for internal microservices
✅ Disable type headers when consuming from non-Spring producers

### Testing Considerations
When writing Kafka consumer tests:
- Mock the deserialization process
- Test with actual JSON strings that Python produces
- Verify Map structure matches expected fields

---

## Service Layer Architecture

### Key Design Patterns

**1. Constructor Injection**
```java
public InventoryService(PartRepository partRepository,
                       InventoryTransactionRepository transactionRepository) {
    this.partRepository = partRepository;
    this.transactionRepository = transactionRepository;
}
```
**Benefits:**
- Easier to test (can pass mocks)
- Required dependencies are explicit
- Spring auto-wires automatically

**2. Transaction Management**
```java
@Service
@Transactional
public class InventoryService {
    // All methods are transactional by default
}
```
**Benefits:**
- Automatic rollback on exceptions
- Database consistency guaranteed
- No manual transaction management

**3. Custom Exceptions**
```java
throw new PartNotFoundException(partNumber);
throw new InsufficientStockException(partNumber, requested, available);
```
**Benefits:**
- Type-safe error handling
- Clear domain semantics
- Easy to catch specific failures

---

## Test-Driven Development (TDD)

### Workflow Followed
1. **Write Test First** → Define expected behavior
2. **Watch It Fail** → Confirms test is actually testing something
3. **Write Implementation** → Minimal code to pass
4. **Watch It Pass** → Confirms implementation works
5. **Refactor** → Improve code without breaking tests

### Testing Layers

**Repository Tests** (`@DataJpaTest`)
- H2 in-memory database
- Tests SQL generation
- Verifies JPQL queries
- Fast (milliseconds per test)

**Service Tests** (`@ExtendWith(MockitoExtension.class)`)
- Mocked repositories
- Tests business logic
- Verifies transactions recorded
- Very fast (no database)

### Mockito Patterns Used

**Stubbing:**
```java
when(partRepository.findByPartNumber("TEST-001"))
    .thenReturn(Optional.of(testPart));
```

**Verification:**
```java
verify(partRepository).save(testPart);
verify(transactionRepository).save(any(InventoryTransaction.class));
```

**Argument Capture:**
```java
ArgumentCaptor<InventoryTransaction> captor =
    ArgumentCaptor.forClass(InventoryTransaction.class);
verify(transactionRepository).save(captor.capture());
assertThat(captor.getValue().getEventId()).isEqualTo("evt-001");
```

---

## Phase 2 Success Metrics

✅ **Database Layer**: JPA entities with proper relationships
✅ **Repository Layer**: 11 passing tests with H2
✅ **Service Layer**: 13 passing tests with Mockito
✅ **Kafka Integration**: Events processed in real-time
✅ **Business Logic**: Stock validation and audit trail
✅ **Error Handling**: Custom exceptions with clear messages
