#!/usr/bin/env python3
"""Detect a repository's stack and existing test coverage by layer.

Standard library only - nothing to install. Works on any repo in any language.

Usage:
    python detect_stack.py [path] [--json] [--max-files N]

Output (human by default) covers:
  languages, package managers, frameworks, test runners and their config files,
  existing test files bucketed into layer guesses, datastores, container and CI
  setup, auth signals, and which layers have no detected coverage.

The layer buckets are heuristics based on path and filename conventions. They are
a starting point for a conversation, not an authority - always confirm by reading
a sample of the files. A file named *.integration.test.ts that mocks the database
is a unit test wearing a costume, and no heuristic can see that.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "bower_components",
    "__pycache__", ".venv", "venv", "env", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", "out", "target",
    ".next", ".nuxt", ".svelte-kit", ".turbo", ".parcel-cache", ".cache",
    "coverage", "htmlcov", ".gradle", ".idea", ".vscode", "Pods",
    "DerivedData", ".terraform", "bin", "obj", ".dart_tool", ".pnpm-store",
    "site-packages", ".angular", ".yarn", "tmp", ".tmp", "test-results",
    "playwright-report", "allure-results", ".nyc_output",
}

# Directories whose contents describe automation, not tests.
NON_TEST_DIR_PREFIXES = (
    ".github/", ".gitlab/", ".circleci/", ".buildkite/", ".husky/",
    "docs/", "doc/", ".changeset/", ".devcontainer/",
)

# Only these extensions can be counted as test *code*.
TEST_CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts",
    ".py", ".go", ".rb", ".php", ".java", ".kt", ".kts", ".scala",
    ".cs", ".fs", ".rs", ".swift", ".dart", ".ex", ".exs", ".erl",
    ".c", ".cpp", ".cc", ".m", ".mm", ".sh", ".bash", ".bats",
    ".feature", ".sql", ".lua", ".pl", ".clj", ".hs", ".jl", ".r",
    ".vue", ".svelte", ".jmx",
}

SNAPSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".snap", ".ambr"}

LANGUAGE_EXTENSIONS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".py": "Python", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala",
    ".cs": "C#", ".fs": "F#", ".rs": "Rust", ".swift": "Swift",
    ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".c": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".m": "Objective-C", ".mm": "Objective-C++",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell",
    ".sql": "SQL", ".tf": "Terraform", ".vue": "Vue", ".svelte": "Svelte",
    ".lua": "Lua", ".pl": "Perl", ".r": "R", ".jl": "Julia",
    ".clj": "Clojure", ".hs": "Haskell", ".zig": "Zig", ".nim": "Nim",
}

MANIFESTS = {
    "package.json": ("JavaScript/TypeScript", "npm"),
    "pnpm-workspace.yaml": ("JavaScript/TypeScript", "pnpm"),
    "pnpm-lock.yaml": ("JavaScript/TypeScript", "pnpm"),
    "yarn.lock": ("JavaScript/TypeScript", "yarn"),
    "package-lock.json": ("JavaScript/TypeScript", "npm"),
    "bun.lockb": ("JavaScript/TypeScript", "bun"),
    "deno.json": ("JavaScript/TypeScript", "deno"),
    "pyproject.toml": ("Python", "pip/poetry/uv"),
    "requirements.txt": ("Python", "pip"),
    "requirements-dev.txt": ("Python", "pip"),
    "Pipfile": ("Python", "pipenv"),
    "setup.py": ("Python", "setuptools"),
    "uv.lock": ("Python", "uv"),
    "poetry.lock": ("Python", "poetry"),
    "go.mod": ("Go", "go modules"),
    "Gemfile": ("Ruby", "bundler"),
    "composer.json": ("PHP", "composer"),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java/Kotlin", "gradle"),
    "build.gradle.kts": ("Java/Kotlin", "gradle"),
    "Cargo.toml": ("Rust", "cargo"),
    "Package.swift": ("Swift", "SwiftPM"),
    "pubspec.yaml": ("Dart/Flutter", "pub"),
    "mix.exs": ("Elixir", "mix"),
    "CMakeLists.txt": ("C/C++", "cmake"),
    "Makefile": ("make-driven", "make"),
    "build.sbt": ("Scala", "sbt"),
    "project.clj": ("Clojure", "leiningen"),
}

RUNNER_CONFIGS = {
    "vitest.config": "Vitest",
    "jest.config": "Jest", "jest.setup": "Jest",
    "playwright.config": "Playwright", "cypress.config": "Cypress",
    "karma.conf": "Karma", ".mocharc": "Mocha",
    "wdio.conf": "WebdriverIO", "codecept.conf": "CodeceptJS",
    "pytest.ini": "pytest", "tox.ini": "tox", "conftest.py": "pytest",
    "phpunit.xml": "PHPUnit", "behat.yml": "Behat",
    ".rspec": "RSpec", "cucumber.yml": "Cucumber",
    "nunit.runsettings": "NUnit", "xunit.runner.json": "xUnit",
    "junit-platform.properties": "JUnit 5",
    "locustfile.py": "Locust", "gatling.conf": "Gatling",
    "detox.config": "Detox",
    "dbt_project.yml": "dbt", "great_expectations.yml": "Great Expectations",
}

# Dependency-name signals. Matched against parsed dependency names.
DEP_SIGNALS = {
    "vitest": "Vitest", "jest": "Jest", "mocha": "Mocha", "jasmine": "Jasmine",
    "@playwright/test": "Playwright", "playwright": "Playwright",
    "cypress": "Cypress", "puppeteer": "Puppeteer", "webdriverio": "WebdriverIO",
    "testing-library": "Testing Library", "axe-core": "axe (a11y)",
    "supertest": "supertest", "testcontainers": "Testcontainers",
    "msw": "MSW (network mocking)", "nock": "nock", "faker": "faker",
    "sinon": "Sinon", "k6": "k6", "artillery": "Artillery",
    "autocannon": "autocannon", "pact": "Pact (consumer contracts)",
    "stryker": "Stryker (mutation testing)",
    "pytest": "pytest", "hypothesis": "Hypothesis (property tests)",
    "responses": "responses", "vcrpy": "VCR.py", "factory-boy": "factory_boy",
    "factory_boy": "factory_boy", "schemathesis": "Schemathesis",
    "locust": "Locust", "mutmut": "mutmut (mutation testing)",
    "rspec": "RSpec", "capybara": "Capybara", "factory_bot": "FactoryBot",
    "database_cleaner": "DatabaseCleaner", "webmock": "WebMock",
    "phpunit": "PHPUnit", "pestphp": "Pest", "mockery": "Mockery",
    "junit": "JUnit", "assertj": "AssertJ", "mockito": "Mockito",
    "archunit": "ArchUnit", "rest-assured": "REST Assured",
    "xunit": "xUnit", "nunit": "NUnit", "fluentassertions": "FluentAssertions",
    "respawn": "Respawn", "bogus": "Bogus",
    "proptest": "proptest", "criterion": "Criterion (benchmarks)",
    "pitest": "PIT (mutation testing)", "testify": "testify",
    "dockertest": "dockertest", "ginkgo": "Ginkgo", "gomega": "Gomega",
}

FRAMEWORK_SIGNALS = {
    "next": "Next.js", "nuxt": "Nuxt", "@remix-run/react": "Remix",
    "@angular/core": "Angular", "react": "React", "vue": "Vue",
    "svelte": "Svelte", "solid-js": "Solid", "astro": "Astro",
    "express": "Express", "fastify": "Fastify", "@nestjs/core": "NestJS",
    "koa": "Koa", "hono": "Hono", "@trpc/server": "tRPC", "graphql": "GraphQL",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "starlette": "Starlette", "celery": "Celery", "streamlit": "Streamlit",
    "rails": "Rails", "sinatra": "Sinatra", "hanami": "Hanami",
    "laravel/framework": "Laravel", "symfony": "Symfony",
    "spring-boot": "Spring Boot", "springframework": "Spring",
    "ktor": "Ktor", "quarkus": "Quarkus", "micronaut": "Micronaut",
    "aspnetcore": "ASP.NET Core",
    "actix-web": "Actix Web", "axum": "Axum", "rocket": "Rocket",
    "gin-gonic": "Gin", "labstack/echo": "Echo", "gofiber": "Fiber",
    "go-chi": "chi", "phoenix": "Phoenix", "flutter": "Flutter",
    "react-native": "React Native", "expo": "Expo",
}

DATASTORE_SIGNALS = {
    "postgres": "PostgreSQL", "pg": "PostgreSQL", "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL", "npgsql": "PostgreSQL", "pgx": "PostgreSQL",
    "mysql": "MySQL", "mariadb": "MariaDB",
    "sqlite": "SQLite", "mongodb": "MongoDB", "mongoose": "MongoDB",
    "pymongo": "MongoDB", "redis": "Redis", "ioredis": "Redis",
    "elasticsearch": "Elasticsearch", "opensearch": "OpenSearch",
    "cassandra": "Cassandra", "dynamodb": "DynamoDB",
    "clickhouse": "ClickHouse", "neo4j": "Neo4j", "kafka": "Kafka",
    "rabbitmq": "RabbitMQ", "amqp": "AMQP", "nats": "NATS",
    "prisma": "Prisma ORM", "typeorm": "TypeORM", "drizzle-orm": "Drizzle ORM",
    "sequelize": "Sequelize", "knex": "Knex", "mikro-orm": "MikroORM",
    "sqlalchemy": "SQLAlchemy", "alembic": "Alembic migrations",
    "activerecord": "ActiveRecord", "hibernate": "Hibernate",
    "entityframework": "Entity Framework", "gorm.io": "GORM",
    "sqlx": "sqlx", "diesel": "Diesel", "ecto": "Ecto",
}

EXTERNAL_SERVICE_SIGNALS = {
    "stripe": "Stripe (payments)", "paypal": "PayPal", "braintree": "Braintree",
    "paymob": "Paymob (payments)", "adyen": "Adyen",
    "nodemailer": "email (SMTP)", "sendgrid": "SendGrid",
    "mailgun": "Mailgun", "postmark": "Postmark", "resend": "Resend",
    "smtplib": "email (SMTP)", "twilio": "Twilio (SMS)",
    "cloudinary": "Cloudinary (media)", "aws-sdk": "AWS SDK",
    "boto3": "AWS (boto3)", "@google-cloud": "Google Cloud",
    "azure": "Azure", "firebase": "Firebase", "supabase": "Supabase",
    "auth0": "Auth0", "clerk": "Clerk", "next-auth": "NextAuth",
    "okta": "Okta", "keycloak": "Keycloak",
    "openai": "OpenAI API", "anthropic": "Anthropic API",
    "algolia": "Algolia", "sentry": "Sentry", "datadog": "Datadog",
    "mapbox": "Mapbox",
}

# Short or English-word keys that must match a dependency name exactly,
# otherwise they fire on unrelated packages ("chi" in "machine", "pg" in "pgp").
EXACT_ONLY = {
    "pg", "koa", "next", "react", "vue", "svelte", "expo", "graphql",
    "azure", "jest", "mocha", "msw", "k6", "sinon", "faker", "nock",
    "redis", "sqlx", "ecto", "junit", "xunit", "nunit", "responses",
    "echo", "chi", "clerk", "okta", "criterion", "mockery", "pact",
    "flask", "django", "celery", "rails", "sinatra", "symfony", "axum",
    "rocket", "ktor", "quarkus", "phoenix", "flutter", "hono", "capybara",
}

CONTAINER_FILES = (
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml", "containerfile", "devcontainer.json",
    "skaffold.yaml", "podman-compose.yml",
)

# Docker image names, matched with word boundaries against compose files.
IMAGE_SIGNALS = {
    "postgres": "PostgreSQL", "mysql": "MySQL", "mariadb": "MariaDB",
    "redis": "Redis", "mongo": "MongoDB", "elasticsearch": "Elasticsearch",
    "opensearch": "OpenSearch", "clickhouse": "ClickHouse",
    "cassandra": "Cassandra", "neo4j": "Neo4j", "kafka": "Kafka",
    "rabbitmq": "RabbitMQ", "nats": "NATS", "minio": "MinIO (S3)",
    "mailhog": "Mailhog (mail sink)", "mailpit": "Mailpit (mail sink)",
    "localstack": "LocalStack (AWS)", "selenium": "Selenium Grid",
}

AUTH_KEYWORDS = (
    "jwt", "session", "csrf", "oauth", "rbac", "permission", "role",
    "tenant", "bearer", "saml", "mfa", "totp",
)

# First matching rule wins - specific before generic.
LAYER_RULES = (
    ("L9",  (r"(^|/)(load|perf|performance|stress|benchmark|bench)(/|$)",
             r"\.k6\.", r"locustfile", r"gatling", r"\.jmx$", r"nbomber")),
    ("L7",  (r"(^|/)(visual|snapshot|screenshot|a11y|accessibility)(/|$)",
             r"(visual|a11y|accessibility|axe|snapshot|percy|responsive|console.?error)",
             r"-snapshots?/", r"__snapshots__/", r"__image_snapshots__/",
             r"(^|/)golden(/|$)")),
    ("L6",  (r"(^|/)(e2e|end.?to.?end|system|acceptance|uitest|uitests)(/|$)",
             r"\.(e2e|cy)\.", r"(^|/)cypress/", r"\.feature$",
             r"xcuitest", r"androidtest", r"(^|/)integration_test/")),
    ("L5",  (r"(^|/)(permission|permissions|authz|authorization|rbac|access.?control|policy|policies)(/|$)",
             r"(permission|authz|authorization|rbac|access.?control|role.?matrix)")),
    ("L8",  (r"(^|/)(concurrency|resilience|chaos|race)(/|$)",
             r"(concurren|resilien|idempoten|race.?condition|chaos|deadlock|transaction.?budget)")),
    ("L3",  (r"(^|/)(contract|contracts|pact|schema|schemas)(/|$)",
             r"(contract|\bpact\b|openapi|swagger|graphql.?schema|json.?schema)")),
    ("L4",  (r"(^|/)(integration|integrations|api|request|requests|functional)(/|$)",
             r"\.(integration|it|api)\.", r"_integration_test\.",
             r"(^|/)spec/requests?/", r"(^|/)test/functional/")),
    ("L2",  (r"(^|/)(component|components|widget|widgets|render)(/|$)",
             r"\.(component|widget|render)\.", r"\.(spec|test)\.(tsx|jsx)$",
             r"(^|/)spec/(views|components|helpers)/", r"robolectric", r"paparazzi",
             r"bunit", r"(^|/)test/widget")),
    ("L10", (r"(^|/)(guard|guards|guardrail|guardrails|drift|golden.?file)(/|$)",
             r"(drift|guardrail|freshness|schema.?sync|budget|config.?guard)")),
    ("L1",  (r".",)),   # fallback
)

TEST_PATH_HINTS = (
    r"(^|/)(tests?|spec|specs|__tests__|testing)(/|$)",
    r"(^|/)src/test(/|$)",
    r"[_.\-](test|spec)s?[_.\-]",
    r"(^|/)test_[^/]*$", r"_test\.", r"\.(test|spec)\.",
    r"\.feature$",
    r"[Tt]ests?\.(cs|java|kt|swift)$",
)

CI_PATHS = {
    ".github/workflows": "GitHub Actions",
    ".gitlab-ci.yml": "GitLab CI",
    ".circleci/config.yml": "CircleCI",
    "azure-pipelines.yml": "Azure Pipelines",
    "Jenkinsfile": "Jenkins",
    ".travis.yml": "Travis CI",
    "bitbucket-pipelines.yml": "Bitbucket Pipelines",
    ".drone.yml": "Drone CI",
    ".buildkite": "Buildkite",
    "cloudbuild.yaml": "Google Cloud Build",
}

LAYER_NAMES = {
    "L0": "Static gates", "L1": "Unit", "L2": "Component", "L3": "Contract",
    "L4": "Integration", "L5": "Authorization", "L6": "End-to-end",
    "L7": "Non-functional UI", "L8": "Resilience", "L9": "Load",
    "L10": "Guardrails",
}
LAYER_ORDER = ("L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10")
CORE_LAYERS = ("L1", "L3", "L4", "L5", "L6", "L8", "L10")

LINT_CONFIG_HINTS = (
    "eslint", ".ruff", "ruff.toml", ".flake8", "pylintrc", "mypy.ini",
    ".rubocop", "phpstan", "psalm.xml", "checkstyle", "ktlint",
    ".golangci", "clippy.toml", ".pre-commit-config.yaml",
    "tsconfig.json", ".prettierrc", "pyrightconfig.json", ".stylelintrc",
    "dependency-cruiser", "sonar-project.properties", ".editorconfig",
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def is_test_path(rel: str) -> bool:
    """True when the path looks like test code (not CI config, not docs)."""
    low = rel.lower()
    if low.startswith(NON_TEST_DIR_PREFIXES):
        return False
    if Path(low).suffix not in TEST_CODE_EXTENSIONS:
        return False
    return any(re.search(p, low) for p in TEST_PATH_HINTS)


def is_snapshot_asset(rel: str) -> bool:
    low = rel.lower()
    if low.startswith(NON_TEST_DIR_PREFIXES):
        return False
    if Path(low).suffix not in SNAPSHOT_EXTENSIONS:
        return False
    return any(re.search(p, low) for p in TEST_PATH_HINTS) or "snapshot" in low


def guess_layer(rel: str) -> str:
    low = rel.lower()
    for layer, patterns in LAYER_RULES:
        if any(re.search(p, low) for p in patterns):
            return layer
    return "L1"


def read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def collect_dependency_names(root: Path, manifests: list[str]) -> set[str]:
    """Parse dependency *names* out of manifests.

    Matching against names rather than raw manifest/lockfile text is what keeps
    `jest-worker` (a transitive Next.js dependency) from reporting "this project
    uses Jest", and `machine` from reporting the Go `chi` router.
    """
    names: set[str] = set()

    for rel in manifests:
        path = root / rel
        base = path.name
        text = read_text(path)
        if not text:
            continue

        if base == "package.json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            for field in ("dependencies", "devDependencies", "peerDependencies",
                          "optionalDependencies"):
                block = data.get(field)
                if isinstance(block, dict):
                    names.update(k.lower() for k in block)

        elif base == "composer.json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            for field in ("require", "require-dev"):
                block = data.get(field)
                if isinstance(block, dict):
                    names.update(k.lower() for k in block)

        elif base in {"requirements.txt", "requirements-dev.txt"}:
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    names.add(re.split(r"[<>=!\[;\s]", line)[0].strip().lower())

        elif base in {"pyproject.toml", "Pipfile", "Cargo.toml", "mix.exs",
                      "pubspec.yaml", "build.sbt", "project.clj"}:
            # Dependency tables across these formats all start a line with the
            # package name; take the leading token of every plausible line.
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", "//", "[")):
                    continue
                match = re.match(r'["\']?([A-Za-z0-9_.:@/\-]+)["\']?\s*[=:{]', stripped)
                if match:
                    names.add(match.group(1).lower())
                match = re.match(r'[:{]?([a-z0-9_]+),?\s*["~>= ]', stripped)
                if match:
                    names.add(match.group(1).lower())

        elif base == "go.mod":
            for line in text.splitlines():
                match = re.match(r"\s*([a-z0-9._~\-]+(?:\.[a-z]{2,})?/[^\s]+)\s+v", line)
                if match:
                    names.add(match.group(1).lower())

        elif base == "Gemfile":
            for match in re.finditer(r'gem\s+["\']([^"\']+)["\']', text):
                names.add(match.group(1).lower())

        elif base in {"pom.xml", "build.gradle", "build.gradle.kts",
                      "Package.swift"}:
            for match in re.finditer(r'<artifactId>([^<]+)</artifactId>', text):
                names.add(match.group(1).lower())
            for match in re.finditer(r'["\']([a-zA-Z0-9._\-]+:[a-zA-Z0-9._\-]+)', text):
                names.add(match.group(1).lower())

    return names


def match_signals(dep_names: set[str], table: dict[str, str]) -> list[str]:
    """Match signal keys against dependency names.

    Keys in EXACT_ONLY need an exact name match (or a scoped/pathed name whose
    final segment matches); everything else may match as a substring.
    """
    found: set[str] = set()
    for key, label in table.items():
        key_low = key.lower()
        for name in dep_names:
            if key_low in EXACT_ONLY:
                segments = {name, name.rsplit("/", 1)[-1], name.rsplit(":", 1)[-1]}
                if key_low in segments:
                    found.add(label)
                    break
            elif key_low in name:
                found.add(label)
                break
    return sorted(found)


def match_images(compose_text: str) -> list[str]:
    low = compose_text.lower()
    return sorted({
        label for key, label in IMAGE_SIGNALS.items()
        if re.search(rf"image:\s*['\"]?[\w./\-]*{re.escape(key)}[\w./\-]*", low)
    })


def walk(root: Path, max_files: int) -> list[str]:
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS
            and not (d.startswith(".") and d not in {".github", ".circleci", ".buildkite", ".devcontainer"})
        ]
        for name in filenames:
            if len(out) >= max_files:
                return out
            try:
                rel = (Path(dirpath) / name).relative_to(root).as_posix()
            except ValueError:
                continue
            out.append(rel)
    return out

# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #


def analyze(root: Path, max_files: int) -> dict:
    files = walk(root, max_files)

    languages: Counter[str] = Counter()
    for rel in files:
        ext = Path(rel).suffix.lower()
        if ext in LANGUAGE_EXTENSIONS:
            languages[LANGUAGE_EXTENSIONS[ext]] += 1

    manifests: list[str] = []
    package_managers: set[str] = set()
    ecosystems: set[str] = set()
    for rel in files:
        base = Path(rel).name
        if base in MANIFESTS:
            eco, pm = MANIFESTS[base]
            manifests.append(rel)
            ecosystems.add(eco)
            package_managers.add(pm)
        elif base.endswith((".csproj", ".fsproj", ".sln")):
            manifests.append(rel)
            ecosystems.add("C#/.NET")
            package_managers.add("nuget")

    dep_names = collect_dependency_names(root, manifests[:60])

    # .NET project files list packages as attributes, not a parsable table.
    dotnet_text = ""
    for rel in manifests:
        if rel.endswith((".csproj", ".fsproj")):
            dotnet_text += "\n" + read_text(root / rel, 80_000)
    for match in re.finditer(r'Include="([^"]+)"', dotnet_text):
        dep_names.add(match.group(1).lower())

    runners = set(match_signals(dep_names, DEP_SIGNALS))
    runner_configs: list[str] = []
    for rel in files:
        name = Path(rel).name.lower()
        for key, tool in RUNNER_CONFIGS.items():
            if name.startswith(key.lower()) or key.lower() in name:
                runners.add(tool)
                runner_configs.append(rel)
                break

    static_configs = sorted({
        rel for rel in files
        if any(hint.lower() in Path(rel).name.lower() for hint in LINT_CONFIG_HINTS)
    })

    container_files = sorted({
        rel for rel in files
        if Path(rel).name.lower() in CONTAINER_FILES
        or Path(rel).name.lower().startswith(("dockerfile", "docker-compose"))
    })
    compose_text = "".join(
        "\n" + read_text(root / rel, 100_000)
        for rel in container_files if "compose" in rel.lower()
    )

    ci = sorted({label for key, label in CI_PATHS.items() if (root / key).exists()})
    ci_workflows = sorted(
        rel for rel in files
        if rel.startswith(".github/workflows/") and rel.endswith((".yml", ".yaml"))
    )

    test_files = [rel for rel in files if is_test_path(rel)]
    snapshot_assets = [rel for rel in files if is_snapshot_asset(rel)]

    layers: dict[str, list[str]] = {key: [] for key in LAYER_NAMES}
    for rel in test_files:
        layers[guess_layer(rel)].append(rel)
    layers["L0"] = static_configs

    datastores = sorted(set(match_signals(dep_names, DATASTORE_SIGNALS))
                        | set(match_images(compose_text)))
    frameworks = match_signals(dep_names, FRAMEWORK_SIGNALS)
    externals = match_signals(dep_names, EXTERNAL_SERVICE_SIGNALS)

    env_text = ""
    for candidate in (".env.example", ".env.sample", ".env.template", ".env.dist"):
        if (root / candidate).is_file():
            env_text += "\n" + read_text(root / candidate, 40_000)
    auth_haystack = (env_text + " " + " ".join(dep_names)).lower()
    auth_signals = sorted({kw for kw in AUTH_KEYWORDS if kw in auth_haystack})

    workspace_globs: list[str] = []
    pkg = root / "package.json"
    scripts: dict[str, str] = {}
    if pkg.is_file():
        try:
            data = json.loads(read_text(pkg))
        except json.JSONDecodeError:
            data = {}
        ws = data.get("workspaces")
        if isinstance(ws, list):
            workspace_globs = [str(w) for w in ws]
        elif isinstance(ws, dict) and isinstance(ws.get("packages"), list):
            workspace_globs = [str(w) for w in ws["packages"]]
        raw = data.get("scripts")
        if isinstance(raw, dict):
            keywords = ("test", "e2e", "lint", "check", "typecheck", "verify",
                        "coverage", "load", "spec")
            scripts = {k: str(v) for k, v in raw.items()
                       if any(t in k.lower() for t in keywords)}
    if (root / "pnpm-workspace.yaml").is_file():
        workspace_globs.append("pnpm-workspace.yaml")
    for marker, label in (("lerna.json", "lerna"), ("nx.json", "nx"),
                          ("turbo.json", "turborepo"), ("rush.json", "rush")):
        if (root / marker).is_file():
            workspace_globs.append(label)

    return {
        "root": str(root),
        "files_scanned": len(files),
        "truncated": len(files) >= max_files,
        "languages": languages.most_common(),
        "ecosystems": sorted(ecosystems),
        "package_managers": sorted(package_managers),
        "manifests": manifests[:40],
        "monorepo": bool(workspace_globs),
        "workspace_markers": workspace_globs,
        "frameworks": frameworks,
        "datastores": datastores,
        "external_services": externals,
        "auth_signals": auth_signals,
        "test_runners": sorted(runners),
        "runner_configs": sorted(set(runner_configs))[:40],
        "static_configs": static_configs[:40],
        "container_files": container_files[:20],
        "ci": ci,
        "ci_workflows": ci_workflows,
        "test_file_count": len(test_files),
        "snapshot_asset_count": len(snapshot_assets),
        "layers": {
            key: {
                "name": LAYER_NAMES[key],
                "count": len(paths),
                "examples": sorted(paths)[:6],
            }
            for key, paths in layers.items()
        },
        "layers_with_no_coverage": [
            f"{key} {LAYER_NAMES[key]}" for key in CORE_LAYERS
            if not layers[key]
        ],
        "existing_test_commands": scripts,
    }

# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def render(report: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add(f"Stack detection - {report['root']}")
    add(f"({report['files_scanned']} files scanned"
        + (", TRUNCATED - raise --max-files" if report["truncated"] else "") + ")")
    add("")

    add("LANGUAGES")
    if report["languages"]:
        for lang, count in report["languages"][:10]:
            add(f"  {lang:<22} {count} files")
    else:
        add("  none recognized")
    add("")

    add("PROJECT")
    monorepo = ("yes - " + ", ".join(report["workspace_markers"][:5])
                if report["monorepo"] else "no")
    for label, value in (
        ("Ecosystems", ", ".join(report["ecosystems"]) or "unknown"),
        ("Package managers", ", ".join(report["package_managers"]) or "unknown"),
        ("Monorepo", monorepo),
        ("Frameworks", ", ".join(report["frameworks"]) or "none detected"),
        ("Datastores", ", ".join(report["datastores"]) or "none detected"),
        ("External services", ", ".join(report["external_services"]) or "none detected"),
        ("Auth signals", ", ".join(report["auth_signals"]) or "none detected"),
        ("Containers", ", ".join(report["container_files"][:6]) or "none"),
    ):
        add(f"  {label:<18}: {value}")
    ci_line = ", ".join(report["ci"]) or "none"
    if report["ci_workflows"]:
        ci_line += f" ({len(report['ci_workflows'])} workflows)"
    add(f"  {'CI':<18}: {ci_line}")
    add("")

    add("TEST TOOLING FOUND")
    add(f"  Runners : {', '.join(report['test_runners']) or 'NONE'}")
    add(f"  Configs : {', '.join(report['runner_configs'][:8]) or 'none'}")
    add("")

    add(f"EXISTING TESTS BY LAYER (heuristic - {report['test_file_count']} test files)")
    for key in LAYER_ORDER:
        info = report["layers"][key]
        mark = "*" if info["count"] else " "
        label = f"{key} {info['name']}"
        add(f" {mark} {label:<26} {info['count']:>4}")
        if info["examples"]:
            add(f"      e.g. {info['examples'][0]}")
    if report["snapshot_asset_count"]:
        add(f"   (plus {report['snapshot_asset_count']} snapshot assets, "
            "not counted as tests)")
    add("")

    if report["existing_test_commands"]:
        add("EXISTING COMMANDS")
        for name, cmd in list(report["existing_test_commands"].items())[:20]:
            shown = cmd if len(cmd) <= 84 else cmd[:81] + "..."
            add(f"  {name:<26} {shown}")
        add("")

    add("CORE LAYERS WITH NO DETECTED COVERAGE")
    gaps = report["layers_with_no_coverage"]
    add("  " + (", ".join(gaps) if gaps else
                "none - every core layer has at least one file"))
    add("")
    add("Heuristics only. Confirm by reading a sample before trusting any count:")
    add("a file named *.integration.test.ts that mocks the database is a unit")
    add("test wearing a costume, and no path heuristic can see that.")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Detect a repo's stack and existing test coverage by layer.")
    parser.add_argument("path", nargs="?", default=".", help="repo root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--max-files", type=int, default=60_000,
                        help="scan ceiling (default: 60000)")
    args = parser.parse_args(argv)

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    report = analyze(root, args.max_files)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    # Windows consoles default to a legacy codepage; keep output lossless.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
