# Stack Map

Concrete tooling per ecosystem. Use it to translate the layer catalogue into
commands that actually exist in the project's language.

**Rules before you pick anything:**

1. **Whatever the repo already uses wins.** A project on Mocha does not get
   migrated to Vitest as part of adding coverage. Extend, don't replace.
2. **Prefer the ecosystem default** when there is no incumbent. Defaults have
   the best documentation, the most Stack Overflow answers, and the least setup.
3. **Prefer zero new services.** If the language has an embedded/in-memory
   option for L4 that behaves like production, weigh it against a container.
4. **One command per layer** — however you achieve it: separate config files,
   test tags/markers, build tags, directory-scoped runs, or separate projects.

---

## JavaScript / TypeScript

| Layer | Tool | One-command mechanism |
| --- | --- | --- |
| L0 | `tsc --noEmit`, ESLint, Prettier, dependency-cruiser / eslint-plugin-boundaries | separate npm scripts |
| L1 | Vitest or Jest (`node` env) | own config file, `include` scoped to unit dir |
| L2 | Vitest/Jest + Testing Library (`jsdom`/`happy-dom` env) | own config, `jsdom` environment |
| L3 | Zod/io-ts/Valibot schema `safeParse` against real responses; `openapi-typescript` regenerate-and-diff | own config |
| L4 | Vitest/Jest node env + `fetch`/supertest against a running app; Testcontainers or docker compose for the datastore | own config, `fileParallelism: false` |
| L5 | Mount the real app (Express/Fastify/Nest/Next handlers) with the data layer mocked; table-driven role × route | own config |
| L6 | Playwright (preferred) or Cypress | `playwright.config.ts` with projects per device |
| L7 | Playwright + `@axe-core/playwright`; `toHaveScreenshot`; console/pageerror listeners | Playwright projects/grep |
| L8 | Vitest + `Promise.all` racing; `vi.mock` for failure injection; Prisma/Knex query event counters | own config |
| L9 | k6 (preferred), Artillery, autocannon | standalone script |
| L10 | Vitest reading migration SQL / config files / generated artifacts | folded into unit config |

**Monorepo note:** put one config per layer at the repo root with explicit
`include` globs and a shared path-alias block, rather than per-package configs —
cross-package integration tests need the root view.

---

## Python

| Layer | Tool |
| --- | --- |
| L0 | `mypy`/`pyright`, `ruff`, `black --check`, `bandit`, `pip-audit` |
| L1 | `pytest` |
| L2 | `pytest` + Django test client templates / Streamlit or Textual harness (UI-dependent) |
| L3 | `pydantic` model validation of real responses; `openapi-spec-validator`; schemathesis for spec-driven fuzzing |
| L4 | `pytest` + `httpx`/`requests` against a live app; `pytest-django --reuse-db`, `testcontainers-python`, or `pytest-postgresql` |
| L5 | `pytest` parametrize over (role, endpoint, expected_status) with the real app via `TestClient`/`APIClient` |
| L6 | Playwright for Python, or Selenium if incumbent |
| L7 | `axe-playwright-python`; `pytest-playwright` snapshot compare |
| L8 | `pytest-asyncio` + `asyncio.gather`; `threading` for sync clients; `pytest-mock` for failure injection; `django-assert-num-queries` for query budgets |
| L9 | Locust (preferred in-ecosystem) or k6 |
| L10 | `pytest` reading migration files / settings modules |

**One-command mechanism:** pytest markers plus strict registration.
`pytest -m integration`, and `--strict-markers` in config so a typo fails loudly.
Alternatively directory-scoped: `pytest tests/integration`.

---

## Go

| Layer | Tool |
| --- | --- |
| L0 | `go vet`, `staticcheck`, `golangci-lint`, `gofmt -l`, `govulncheck` |
| L1 | stdlib `testing` + table-driven tests |
| L2 | n/a usually; templ/html rendering asserted as L1 |
| L3 | `oapi-codegen` regenerate-and-diff; JSON schema validation |
| L4 | `httptest.Server` + `dockertest`/Testcontainers-Go; or `t.Parallel()`-safe schema-per-test |
| L5 | table-driven over roles hitting the real `http.Handler` via `httptest` |
| L6 | `chromedp`, Playwright-Go, or Rod |
| L7 | Playwright-Go + axe injection |
| L8 | `sync.WaitGroup` concurrent hammering; `-race` always on |
| L9 | k6 or `vegeta` |
| L10 | `testing` reading migration/config files; `go:embed` for golden files |

**One-command mechanism:** build tags (`//go:build integration` + `go test -tags
integration ./...`) or `-run` regex on a naming convention.
Always run unit with `-race`.

---

## Ruby

| Layer | Tool |
| --- | --- |
| L0 | RuboCop, Sorbet/RBS, `brakeman`, `bundler-audit` |
| L1 | RSpec (or Minitest if incumbent) |
| L2 | ViewComponent specs / RSpec view specs |
| L3 | `rswag` / committee for OpenAPI conformance |
| L4 | RSpec request specs with a real test database (`ActiveRecord` transactional fixtures, or `DatabaseCleaner` truncation) |
| L5 | RSpec request specs parameterized over roles via `shared_examples` |
| L6 | Capybara + Cuprite/Selenium; or Playwright-Ruby |
| L7 | `axe-core-rspec`; `percy`/`happo` for visual if budgeted |
| L8 | threads + `ActiveRecord` locking assertions; `Bullet` for N+1 |
| L9 | k6 or `siege` |
| L10 | specs reading `db/structure.sql` and config initializers |

**One-command mechanism:** RSpec tags (`bundle exec rspec --tag integration`) or
directory-scoped (`spec/requests`, `spec/system`).

---

## PHP / Laravel / Symfony

| Layer | Tool |
| --- | --- |
| L0 | PHPStan/Psalm, PHP-CS-Fixer, `composer audit` |
| L1 | PHPUnit or Pest |
| L2 | Blade/Twig component rendering assertions |
| L3 | JSON schema assertions; `spectator` for OpenAPI |
| L4 | Laravel feature tests with `RefreshDatabase` against real MySQL/Postgres (not SQLite — driver differences hide bugs) |
| L5 | feature tests over a role dataset via PHPUnit data providers |
| L6 | Laravel Dusk, or Playwright driving `artisan serve` |
| L7 | Playwright + axe |
| L8 | `DB::transaction` + concurrent HTTP via parallel processes; queue failure injection with `Queue::fake()` partial |
| L9 | k6 |
| L10 | tests reading migration files and `config/*.php` |

**One-command mechanism:** PHPUnit `<testsuite>` blocks in `phpunit.xml`, then
`--testsuite=Integration`.

---

## Java / Kotlin

| Layer | Tool |
| --- | --- |
| L0 | compiler `-Werror`, Checkstyle/ktlint, SpotBugs, ArchUnit for boundaries, OWASP dependency-check |
| L1 | JUnit 5 + AssertJ |
| L2 | Compose UI test / Android `ComposeTestRule`; Thymeleaf render tests server-side |
| L3 | Spring Cloud Contract, or springdoc regenerate-and-diff |
| L4 | `@SpringBootTest` + Testcontainers (the gold standard here) |
| L5 | `@WebMvcTest`/`MockMvc` with `@WithMockUser` parameterized over roles |
| L6 | Playwright-Java or Selenide |
| L7 | axe via Playwright; Espresso/Compose for mobile |
| L8 | `CompletableFuture`/`ExecutorService` concurrency tests; Awaitility for conditions; Hibernate statistics for query budgets |
| L9 | Gatling (in-ecosystem) or k6 |
| L10 | ArchUnit rules + tests reading Flyway/Liquibase scripts |

**One-command mechanism:** JUnit 5 `@Tag` + Gradle/Maven task per tag
(`./gradlew integrationTest`). ArchUnit is the best boundary tool in any
ecosystem — use it for L0 if this is a Java/Kotlin project.

---

## C# / .NET

| Layer | Tool |
| --- | --- |
| L0 | `dotnet build -warnaserror`, Roslyn analyzers, `dotnet format --verify-no-changes`, NetArchTest |
| L1 | xUnit (preferred) / NUnit + FluentAssertions |
| L2 | bUnit for Blazor |
| L3 | Swashbuckle regenerate-and-diff; PactNet |
| L4 | `WebApplicationFactory<T>` + Testcontainers, or Respawn to reset the database |
| L5 | `WebApplicationFactory` with a test auth handler, `[Theory]` over roles |
| L6 | Playwright for .NET |
| L7 | axe via Playwright |
| L8 | `Task.WhenAll` races; EF Core interceptors for query counts |
| L9 | NBomber or k6 |
| L10 | tests reading EF migrations and `appsettings.*.json` |

**One-command mechanism:** `[Trait("Layer","Integration")]` + `dotnet test
--filter "Layer=Integration"`, or separate test projects per layer.

---

## Rust

| Layer | Tool |
| --- | --- |
| L0 | `cargo clippy -- -D warnings`, `cargo fmt --check`, `cargo audit`, `cargo deny` |
| L1 | `#[cfg(test)]` inline unit tests |
| L2 | n/a mostly; Leptos/Yew have wasm test harnesses |
| L3 | `utoipa`/`schemars` regenerate-and-diff; `serde` round-trip tests |
| L4 | `tests/` integration dir + `sqlx::test` (transaction-per-test) or Testcontainers-rs |
| L5 | tower/axum service tests with a role table |
| L6 | `thirtyfour` (WebDriver) or Playwright driven externally |
| L7 | external Playwright |
| L8 | `tokio::join!`/`spawn` races; `loom` for lock-level concurrency verification |
| L9 | k6 or `oha`/`drill` |
| L10 | tests reading migration files with `include_str!` |

**One-command mechanism:** `cargo test --test integration` (files in `tests/`
are separate binaries — this is the cleanest layer isolation of any ecosystem).

---

## Mobile

| | iOS (Swift) | Android (Kotlin) | Flutter | React Native |
| --- | --- | --- | --- | --- |
| L1 | XCTest / Swift Testing | JUnit + kotlin.test | `flutter test` | Jest |
| L2 | ViewInspector / snapshot-testing | Compose UI Test / Robolectric | widget tests | RNTL |
| L4 | XCTest + local server or stub | Retrofit + MockWebServer | `integration_test` | Jest + MSW |
| L6 | XCUITest | Espresso / UI Automator | `integration_test` on device | Detox / Maestro |
| L7 | Accessibility Inspector audits; snapshot tests | Accessibility Scanner; Paparazzi | golden files | Detox + a11y props |
| L9 | XCTest metrics | Macrobenchmark | — | — |

Mobile inverts the usual economics: L6 on real devices is expensive and slow, so
push aggressively into L2 (screenshot/snapshot tests of composables/views) and
keep device E2E to the two or three journeys that gate a release.

---

## Data / ETL / notebooks

| Layer | Approach |
| --- | --- |
| L0 | `sqlfluff`, `ruff`, schema linting |
| L1 | transform functions tested on small in-memory frames |
| L3 | schema contracts: `pandera`, Great Expectations, dbt `schema.yml` tests |
| L4 | run the pipeline against a small fixture warehouse; assert row counts and invariants |
| L8 | idempotency: run the pipeline twice, assert identical output (the #1 ETL bug) |
| L10 | freshness and null-rate guards on the real warehouse |

Golden-file testing is the backbone here: a committed input fixture and a
committed expected output, with an explicit regeneration command.

---

## Infrastructure as code

| Layer | Approach |
| --- | --- |
| L0 | `terraform validate`, `tflint`, `checkov`/`tfsec`, `kubeval`/`kubeconform` |
| L1 | Terraform `plan` assertions; OPA/Conftest policies against the plan JSON |
| L4 | Terratest / `terraform test` provisioning real ephemeral resources |
| L6 | post-deploy smoke checks against the provisioned environment |
| L10 | drift detection on a schedule (`plan` must be empty) |

---

## Shell / CLI tools

| Layer | Approach |
| --- | --- |
| L0 | `shellcheck`, `shfmt -d` |
| L1 | `bats-core` (bash), or the language's own runner |
| L4 | invoke the built binary in a temp dir; assert stdout, stderr, exit code, and files created |
| L6 | full-workflow script exercising the documented README commands |
| L10 | `--help` output snapshot, so flags can't vanish silently |

Assert **exit codes** first — the most common CLI bug is succeeding loudly while
failing.

---

## No recognized stack / legacy

When detection finds nothing usable:

1. Find how the project is built and run today (README, Makefile, CI config,
   Dockerfile, a script somebody runs by hand).
2. Start at L4 from the outside: drive the app through its real interface
   (HTTP, CLI, file drop) and assert observable outcomes. This needs no test
   framework inside the codebase and works on code you cannot refactor.
3. Add L0 next — a linter for the language, however old.
4. Only then work inward to L1 as you touch code.

Characterization tests come before refactoring: capture what the system does
*today* (even if wrong), so a refactor that changes behaviour fails visibly.
Record any captured-but-suspicious behaviour explicitly as a question, not as
an endorsement.
