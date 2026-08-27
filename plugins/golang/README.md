# Go plugin

Go code standards enforcement: a strict review checklist, a build orchestrator,
four specialist agents and automatic formatting.

Installed as `golang@kodflow`; its components are prefixed by the plugin name
(`/golang:review`, `/golang:build`).

## What ships in this plugin

| Component | File | Invocation |
| --------- | ---- | ---------- |
| Command | `commands/review.md` | `/golang:review` — professional Go code review |
| Command | `commands/build.md` | `/golang:build` — orchestrated development with task tracking |
| Agent | `agents/go-expert.md` | Go 1.23–1.25 language features |
| Agent | `agents/ddd-architect.md` | Domain-driven structure enforcement |
| Agent | `agents/code-reviewer.md` | Quality standards review |
| Agent | `agents/performance-optimizer.md` | Performance and allocation analysis |
| Hook | `hooks/hooks.json` | `PostToolUse` — runs `gofmt` and `goimports` on written `.go` files |
| MCP | `.mcp.json` | `github` and `codacy` servers |
| Reference | `GO_STANDARDS.md` | Quick reference guide |

### MCP environment variables

The `.mcp.json` servers read two variables; without them the servers fail to
start and the rest of the plugin still works.

| Variable | Used by | Where to get it |
| -------- | ------- | --------------- |
| `GITHUB_TOKEN` | `github` server | <https://github.com/settings/tokens> |
| `CODACY_API_TOKEN` | `codacy` server | <https://app.codacy.com/account/apiTokens> |

## Key rules

### 1. Package descriptor

Every `.go` file starts with a descriptor. Features must be declared before the
matching capability is used — using telemetry without declaring it is flagged in
review.

```go
// Package <name> <description>
//
// Purpose:
//   <What it does>
//
// Responsibilities:
//   - <Responsibility 1>
//
// Features:
//   - <Feature 1>  (Metrics, Tracing, Database, etc.)
//
// Constraints:
//   - <Constraint 1>
//
package <name>
```

Declarable features: `Metrics`, `Tracing`, `Logging`, `Database`, `Validation`,
`HTTP`, `Caching`, `RateLimiting`, `CircuitBreaker`, `Retry`, `Authentication`,
`gRPC`, `PubSub`.

### 2. Code metrics

- Functions under 35 lines (strict)
- Cyclomatic complexity under 10 (`gocyclo -over 9 .`)
- 100 % test coverage

### 3. One file per struct

```
package/
├── constants.go           # ALL constants
├── errors.go              # ALL errors
├── interfaces.go          # ALL interfaces
├── interfaces_test.go     # ALL mocks (package xxx_test)
├── user.go                # User struct + methods
├── user_test.go           # User tests
├── order.go               # Order struct + methods
└── service.go             # Main service orchestration
```

No `models.go` holding several structs: one file per struct means clearer
ownership and fewer merge conflicts.

Test files use the black-box form:

```go
package taskqueue_test   // correct

package taskqueue        // wrong — do not use the same package
```

### 4. Constructor pattern

```go
type ServiceConfig struct {
    Dep1 Interface1
    Val1 string
}

func NewService(cfg ServiceConfig) (*Service, error) {
    // validate all required fields
    return &Service{...}, nil
}
```

Prefer `NewService(cfg)` over a bare `&Service{...}`.

## Quality gates

All of these must pass:

```bash
gocyclo -over 9 .
golangci-lint run
go vet ./...
staticcheck ./...
gosec ./...
go test -race ./...
go test -cover -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total   # must be 100%
```

## Usage

```bash
/golang:review                  # review changed files
/golang:review path/to/file.go  # review a specific file
/golang:review --full           # full codebase review
/golang:build                   # orchestrated development with task tracking
```

### Example: service without telemetry

```go
// Package userservice provides user management
//
// Purpose:
//   User CRUD operations
//
// Responsibilities:
//   - User creation and validation
//
// Features:
//   - Database
//   - Validation
//   - Logging
//
package userservice

// no telemetry imports — clean
```

### Example: service with telemetry

```go
// Package userservice provides user management with observability
//
// Purpose:
//   User CRUD operations with full observability
//
// Responsibilities:
//   - User creation and validation
//   - Metrics collection
//
// Features:
//   - Metrics        // explicitly declared
//   - Tracing        // explicitly declared
//   - Database
//
package userservice

import (
    "go.opentelemetry.io/otel/metric"  // ok — Metrics declared
    "go.opentelemetry.io/otel/trace"   // ok — Tracing declared
)
```

## Common violations

1. Missing package descriptor
2. Undeclared telemetry usage
3. Function over 35 lines
4. Complexity over 9
5. Coverage under 100 %
6. Missing constructor
7. Wrong file structure
8. Ignored errors

## Checklist before submitting

- [ ] Package descriptor on every `.go` file
- [ ] Features explicitly declared, and none used without declaration
- [ ] All functions under 35 lines and complexity under 10
- [ ] 100 % test coverage
- [ ] `interfaces.go` with all interfaces, `interfaces_test.go` with all mocks
- [ ] Every struct has its `NewXxx()`; services take an `XxxConfig`
- [ ] No ignored errors
- [ ] `golangci-lint`, `gosec` and `go test -race` pass

## Review process

1. **Automated checks** — tools run first
2. **Package descriptor** — declaration versus actual usage
3. **Structural compliance** — file organisation
4. **Manual checks** — comprehensive review
5. **Testability** — coverage verification
6. **Verdict** — approved, or rejected with fixes
