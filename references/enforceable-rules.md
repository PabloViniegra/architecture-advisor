# Enforceable Rules per Architecture

Every architecture below ships with **enforceable rules**, not just prose. When writing the `## Architecture` section in CLAUDE.md/AGENTS.md and the ADR, copy the relevant rule set and adapt names to the user's actual domain.

Each entry has three parts:
- **Dependency rules** — what may import what (the backbone an agent or linter can enforce)
- **Placement rules** — where each kind of code lives
- **Linter config** — a ready-to-drop config for the project's stack, if the user wants tooling (Phase 3.4)

Pick the linter that matches the language:
- **TS/JS** → `dependency-cruiser` (`.dependency-cruiser.js`)
- **Python** → `import-linter` (`.importlinter` / `setup.cfg` section)
- **Go** → `go-arch-lint` (`.go-arch-lint.yml`)

> ⚠️ **All folder paths in this file are illustrative.** The regex patterns assume a common layout (e.g. `^src/domain`, `modules/<name>/`). Before generating or copying any linter config, substitute the actual folder names from the user's project. Common variations to watch for:
> - Go projects: typically `internal/`, `cmd/`, `pkg/` — not `src/`
> - Python packages: often a flat `<package_name>/` at root — not `src/`
> - Monorepos: may use `apps/`, `packages/`, `services/` as the top level
> - Java/Kotlin: `src/main/java/<groupId>/` nested structure
>
> Always verify the real structure from Phase 0 detection before emitting a linter config.

---

## Layered (N-Tier)

**Dependency rules**
- `presentation/` → may import `application/` only
- `application/` → may import `domain/` only
- `domain/` → imports nothing internal (pure)
- `infrastructure/` → may import `domain/` (implements its interfaces); nothing imports `infrastructure/` directly except composition root

**Placement rules**
- Controllers/handlers → `presentation/`
- Use cases / services → `application/`
- Entities, value objects, domain interfaces → `domain/`
- DB, HTTP clients, framework glue → `infrastructure/`
- Wiring → `main`/`bootstrap`/composition root only

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'domain-is-pure', from: { path: '^src/domain' }, to: { path: '^src/(application|presentation|infrastructure)' } },
    { name: 'app-no-presentation', from: { path: '^src/application' }, to: { path: '^src/presentation' } },
    { name: 'no-infra-leak', from: { pathNot: '^src/(infrastructure|main)' }, to: { path: '^src/infrastructure' } },
  ],
};
```

---

## Modular Monolith

**Dependency rules**
- Each module under `modules/<name>/` is a vertical slice. Modules **must not** import each other's internals.
- Cross-module communication only through a published interface: `modules/<name>/public/` (or via events).
- Shared kernel lives in `shared/` and may be imported by any module; `shared/` imports no module.

**Placement rules**
- All code for a business capability lives inside its module folder, including its own `domain/`, `application/`, `infrastructure/`.
- A module exposes exactly one entry surface (`public/index.ts` / `public.go`).

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'module-encapsulation',
      comment: 'Modules may only touch another module via its public surface',
      from: { path: '^src/modules/([^/]+)/' },
      to: { path: '^src/modules/(?!\\1/)([^/]+)/(?!public)' } },
    { name: 'shared-is-leaf', from: { path: '^src/shared' }, to: { path: '^src/modules' } },
  ],
};
```

**go-arch-lint** (sketch)
```yaml
components:
  billing: { in: modules/billing/** }
  shipping: { in: modules/shipping/** }
  shared:   { in: shared/** }
deps:
  billing:  { mayDependOn: [shared] }
  shipping: { mayDependOn: [shared] }
```

---

## Clean Architecture

**Dependency rules** (the Dependency Rule — dependencies point inward only)
- `entities/` (innermost) → imports nothing
- `usecases/` → may import `entities/`
- `adapters/` (controllers, presenters, gateways) → may import `usecases/` + `entities/`
- `frameworks/` (DB, web, external) → outermost; imports inward, nothing imports it except composition root
- Inner layers define interfaces; outer layers implement them (Dependency Inversion)

**Placement rules**
- Business rules independent of everything → `entities/`
- Application-specific rules / orchestration → `usecases/`
- Interface adapters that convert data across boundaries → `adapters/`
- DB drivers, web framework, third-party SDKs → `frameworks/`

**import-linter** (Python)
```ini
[importlinter]
root_package = app
[importlinter:contract:clean-layers]
name = Clean Architecture layers
type = layers
layers =
    app.frameworks
    app.adapters
    app.usecases
    app.entities
```

---

## Hexagonal / Ports & Adapters

**Dependency rules**
- `core/` (domain + application) defines **ports** (interfaces). It imports no adapter.
- `adapters/driving/` (HTTP, CLI, queue consumers) call into core ports.
- `adapters/driven/` (DB, message publishers, external APIs) implement core ports.
- Nothing in `core/` references a concrete adapter — only ports.

**Placement rules**
- Domain logic + port interfaces → `core/`
- Inbound adapters (anything that triggers the app) → `adapters/driving/`
- Outbound adapters (anything the app calls) → `adapters/driven/`
- Wiring of ports to adapters → composition root only

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'core-knows-no-adapters', from: { path: '^src/core' }, to: { path: '^src/adapters' } },
    { name: 'driving-cant-touch-driven', from: { path: '^src/adapters/driving' }, to: { path: '^src/adapters/driven' } },
  ],
};
```

---

## Screaming Architecture

**Dependency rules**
- Top-level folders are **business capabilities** (`invoicing/`, `onboarding/`), never technical layers (`controllers/`, `services/`).
- A capability may depend on `shared/` but not reach into another capability's internals.
- Framework code is pushed to the edges; the top level "screams" the domain.

**Placement rules**
- New feature → new top-level domain folder, not a new file scattered across technical layers.
- Inside each capability you may still apply Clean/Layered internally.

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'no-technical-toplevel',
      comment: 'Top-level folders must be domains, not layers',
      from: {}, to: { path: '^src/(controllers|services|repositories|models)/' } },
  ],
};
```

---

## DDD (Domain-Driven Design)

**Dependency rules**
- Each **bounded context** is isolated; contexts integrate only via published language / anti-corruption layers (`acl/`), never by importing another context's domain.
- Within a context: `domain/` (aggregates, value objects, domain services, repository interfaces) imports nothing technical.
- `application/` orchestrates aggregates; `infrastructure/` implements repositories.

**Placement rules**
- Aggregates, entities, value objects, domain events, repository interfaces → `domain/`
- Application services / command handlers → `application/`
- Repository implementations, ORM, external context clients → `infrastructure/`
- Translation between contexts → `acl/`

**import-linter** (Python)
```ini
[importlinter:contract:context-isolation]
name = Bounded contexts are independent
type = independence
modules =
    app.contexts.billing
    app.contexts.catalog
    app.contexts.shipping
```

---

## Microservices

**Dependency rules**
- Services share **no code at the domain level**. Only versioned contracts (OpenAPI, protobuf, event schemas) are shared, via a `contracts/` package.
- No service reaches into another service's database (database-per-service).
- Cross-service calls go through an explicit client generated from the contract.

**Placement rules**
- Each service is its own deployable with its own internal architecture.
- Shared contracts → a dedicated repo or `contracts/` package, versioned.

**Enforcement** — Microservices coupling is best caught at the CI/network level, not import-level. Three complementary approaches:

```yaml
# 1. CI script: assert no service imports another service's source
# Add to .github/workflows/lint.yml or equivalent:
#   - name: Check service source isolation
#     run: |
#       for svc in services/*/; do
#         name=$(basename $svc)
#         if grep -rE "from services\.[^${name}]" "services/${name}/" 2>/dev/null; then
#           echo "❌ ${name} imports from another service's source"
#           exit 1
#         fi
#       done
```

```yaml
# 2. go-arch-lint (Go monorepo) — each service is its own component
# .go-arch-lint.yml
components:
  billing:  { in: services/billing/** }
  shipping: { in: services/shipping/** }
  shared:   { in: shared/** }
deps:
  billing:  { mayDependOn: [shared] }
  shipping: { mayDependOn: [shared] }
# Any cross-service dep must go through shared contracts, not source
```

```js
// 3. dependency-cruiser (TS/JS monorepo)
module.exports = {
  forbidden: [
    { name: 'no-cross-service-source',
      comment: 'Services communicate via contracts, not source imports',
      from: { path: '^services/([^/]+)' },
      to: { path: '^services/(?!\\1)[^/]+/(src|lib|internal)' } },
  ],
};
```

---

## MVC / MVP / MVVM

**Dependency rules**
- `views/` → no business logic; render only.
- `controllers/` (or presenters/viewmodels) → coordinate; import `models/`.
- `models/` → domain + data; import nothing from views/controllers.

**Placement rules**
- Templates/components → `views/`
- Request handling / view-model state → `controllers/` or `viewmodels/`
- Business + persistence → `models/`

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'models-have-no-ui', from: { path: '^src/models' }, to: { path: '^src/(views|controllers)' } },
    { name: 'views-have-no-logic', from: { path: '^src/views' }, to: { path: '^src/models' } },
  ],
};
```

**import-linter** (Python)
```ini
[importlinter]
root_package = app
[importlinter:contract:mvc-layers]
name = MVC layer isolation
type = layers
layers =
    app.views
    app.controllers
    app.models
```

**Dependency rules**
- `commands/` (write side) and `queries/` (read side) are fully separate; neither imports the other.
- Write side mutates aggregates; read side reads from denormalised read models only.
- A read model is never written by the query side; only projections (fed by events) update it.

**Placement rules**
- Command handlers + write model → `commands/`
- Query handlers + read models / DTOs → `queries/`
- Projections that sync read models → `projections/`

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'cqrs-separation', from: { path: '^src/commands' }, to: { path: '^src/queries' } },
    { name: 'cqrs-separation-rev', from: { path: '^src/queries' }, to: { path: '^src/commands' } },
  ],
};
```

---

## Event-Driven / EDA

**Dependency rules**
- Producers depend only on the **event schema**, never on consumers.
- Consumers depend only on the event schema, never on the producer's internals.
- Event contracts live in a shared `events/` package, versioned; breaking changes require a new event version.

**Placement rules**
- Event definitions/schemas → `events/`
- Publishers → inside the owning module, importing only `events/`
- Subscribers/handlers → `handlers/` within the consuming module

**Enforcement**
```js
// dependency-cruiser
module.exports = {
  forbidden: [
    { name: 'no-producer-consumer-coupling',
      from: { path: '^src/modules/([^/]+)' },
      to: { path: '^src/modules/(?!\\1)[^/]+/(handlers|internal)' } },
  ],
};
```

---

## Pipeline / Pipes & Filters

**Dependency rules**
- Each stage (`filter`) depends only on the data contract of its input and output, not on other stages.
- Stages are composable and order-independent in code (order defined by the pipeline assembler only).

**Placement rules**
- Each transformation → its own `stages/<name>.py`
- Pipeline composition → `pipeline.py` / orchestrator only
- Shared record schemas → `schemas/`

**dependency-cruiser** (TS/JS)
```js
module.exports = {
  forbidden: [
    { name: 'stages-are-isolated',
      comment: 'Pipeline stages must not import each other — only the orchestrator composes them',
      from: { path: '^src/stages/([^/]+)' },
      to: { path: '^src/stages/(?!\\1)[^/]+' } },
    { name: 'stages-use-shared-schemas',
      comment: 'Stage I/O contracts live in schemas/, not inlined per-stage',
      from: { path: '^src/stages' }, to: { path: '^src/stages/.+/schema' } },
  ],
};
```

**import-linter** (Python)
```ini
[importlinter]
root_package = pipeline
[importlinter:contract:stage-isolation]
name = Pipeline stages are independent
type = independence
modules =
    pipeline.stages.extract
    pipeline.stages.transform
    pipeline.stages.load
```

**Dependency rules**
- Each function depends only on `shared/` + its own handler code; functions never import each other.
- Business logic lives in `shared/` (testable without the cloud runtime); handlers are thin adapters.

**Placement rules**
- Cloud entry points (thin) → `functions/<name>/handler.*`
- Reusable domain logic → `shared/`
- Infra-as-code → `infra/`

**dependency-cruiser**
```js
module.exports = {
  forbidden: [
    { name: 'functions-are-isolated',
      from: { path: '^functions/([^/]+)' },
      to: { path: '^functions/(?!\\1)[^/]+' } },
    { name: 'handlers-stay-thin',
      comment: 'Move logic to shared/ — handlers should delegate',
      from: { path: 'handler\\.(ts|js)$' }, to: { path: 'node_modules/(pg|mongodb|axios)' } },
  ],
};
```

---

## Space-Based

**Dependency rules**
- Processing units are self-contained and stateless toward each other; they coordinate only through the shared in-memory data grid.
- No processing unit imports another; the grid is the only integration point.

**Placement rules**
- Processing unit logic → `units/<name>/`
- Grid access layer → `grid/`
- Deployment/replication config → `infra/`

**dependency-cruiser** (TS/JS)
      comment: 'Processing units coordinate only through the data grid, never directly',
      from: { path: '^src/units/([^/]+)' },
      to: { path: '^src/units/(?!\\1)[^/]+' } },
    { name: 'units-use-grid-layer',
      comment: 'Grid access must go through the grid/ abstraction layer',
      from: { path: '^src/units' }, to: { pathNot: '^src/(units|grid|shared)' } },
  ],
};
```

> ⚠️ Space-Based is rare in typical business applications. If you find yourself here, confirm with the team that the complexity is genuinely warranted before proceeding.

1. Copy the matching rule block into the `### Rules for contributors` of the agent config file and the `## Implementation notes` of the ADR — adapting folder/domain names to the user's project.
2. If the user opts into tooling (Phase 3.4), generate the linter config file for their stack and add a short note on how to run it (`npx depcruise`, `lint-imports`, `go-arch-lint check`).
3. For hybrids, merge the rule sets — e.g. Modular Monolith + Clean means module-encapsulation rules **and** inner-layer dependency rules inside each module.
