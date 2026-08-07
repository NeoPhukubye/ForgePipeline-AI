"""
Intelligent Dockerfile generator that produces optimized, multi-stage,
security-hardened Dockerfiles based on code analysis results.
"""

from .analyzer import AnalysisResult


class DockerfileGenerator:
    """Generates production-quality Dockerfiles based on AnalysisResult."""

    def generate(self, analysis: AnalysisResult) -> str:
        generators = {
            "python": self._generate_python,
            "javascript": self._generate_node,
            "typescript": self._generate_node,
            "go": self._generate_go,
            "rust": self._generate_rust,
            "java": self._generate_java,
        }

        generator = generators.get(analysis.language, self._generate_generic)
        return generator(analysis)

    def _generate_python(self, a: AnalysisResult) -> str:
        python_ver = a.python_version or "3.12"
        base = f"python:{python_ver}-slim"

        install_cmd = self._python_install_cmd(a)
        start_cmd = a.start_command or "python main.py"

        lines = [
            f"FROM {base} AS base",
            "",
            "ENV PYTHONDONTWRITEBYTECODE=1 \\",
            "    PYTHONUNBUFFERED=1",
            "",
            "WORKDIR /app",
            "",
            "RUN addgroup --system app && adduser --system --ingroup app app",
            "",
            "# Install dependencies",
            "FROM base AS deps",
        ]

        if a.package_manager == "poetry":
            lines += [
                "RUN pip install --no-cache-dir poetry",
                "COPY pyproject.toml poetry.lock* ./",
                "RUN poetry config virtualenvs.create false \\",
                "    && poetry install --no-dev --no-interaction --no-ansi",
            ]
        elif a.package_manager == "uv":
            lines += [
                "COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv",
                "COPY pyproject.toml uv.lock* ./",
                "RUN uv sync --frozen --no-dev",
            ]
        else:
            lines += [
                "COPY requirements.txt .",
                f"RUN {install_cmd}",
            ]

        lines += [
            "",
            "# Final stage",
            "FROM base AS runtime",
            (
                "COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages"
                if a.package_manager != "uv"
                else "COPY --from=deps /app/.venv /app/.venv"
            ),
            "COPY . .",
            "",
            "USER app",
            f"EXPOSE {a.port or 8000}",
            "",
            f"CMD {self._to_cmd_array(start_cmd)}",
        ]

        return "\n".join(lines) + "\n"

    def _generate_node(self, a: AnalysisResult) -> str:
        node_ver = a.node_version or "22"
        if "-" in node_ver or ">" in node_ver or "<" in node_ver:
            node_ver = "22"
        pm = a.package_manager or "npm"

        # Static site (React/Vue with Vite) vs server app
        if a.static_output_dir:
            return self._generate_node_static(a, node_ver, pm)
        return self._generate_node_server(a, node_ver, pm)

    def _generate_node_static(self, a: AnalysisResult, node_ver: str, pm: str) -> str:
        install, build = self._node_commands(pm, a)
        output_dir = a.static_output_dir or "dist"

        return f"""FROM node:{node_ver}-alpine AS builder

WORKDIR /app
{self._node_copy_lockfile(pm)}
COPY package.json .
RUN {install}

COPY . .
RUN {build}

# Serve with nginx
FROM nginx:alpine AS runtime

COPY --from=builder /app/{output_dir} /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {{
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}

    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
EOF

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

    def _generate_node_server(self, a: AnalysisResult, node_ver: str, pm: str) -> str:
        install, build = self._node_commands(pm, a)
        start_cmd = a.start_command or "node index.js"
        port = a.port or 3000

        lines = f"""FROM node:{node_ver}-alpine AS deps

WORKDIR /app
{self._node_copy_lockfile(pm)}
COPY package.json .
RUN {install}

FROM node:{node_ver}-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
"""
        if build:
            lines += f"RUN {build}\n"

        lines += f"""
FROM node:{node_ver}-alpine AS runtime
WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder /app .
{"RUN " + install.replace("install", "install --production") if pm == "npm" else ""}

USER app
EXPOSE {port}
CMD {self._to_cmd_array(start_cmd)}
"""
        return lines

    def _generate_go(self, a: AnalysisResult) -> str:
        return f"""FROM golang:1.23-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app .

FROM scratch AS runtime
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app /app

EXPOSE {a.port or 8080}
ENTRYPOINT ["/app"]
"""

    def _generate_rust(self, a: AnalysisResult) -> str:
        return f"""FROM rust:1.79-slim AS builder

WORKDIR /src
COPY Cargo.toml Cargo.lock ./

# Cache dependency build
RUN mkdir src && echo "fn main() {{}}" > src/main.rs
RUN cargo build --release && rm -rf src

COPY . .
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -s /bin/false app
COPY --from=builder /src/target/release/app /usr/local/bin/app

USER app
EXPOSE {a.port or 8080}
CMD ["app"]
"""

    def _generate_java(self, a: AnalysisResult) -> str:
        if a.package_manager == "maven":
            build_stage = """FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /src
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY . .
RUN mvn clean package -DskipTests -B"""
        else:
            build_stage = """FROM gradle:8-jdk21 AS builder
WORKDIR /src
COPY build.gradle settings.gradle ./
RUN gradle dependencies --no-daemon
COPY . .
RUN gradle build -x test --no-daemon"""

        return f"""{build_stage}

FROM eclipse-temurin:21-jre-alpine AS runtime
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app

COPY --from=builder /src/target/*.jar app.jar

USER app
EXPOSE {a.port or 8080}
CMD ["java", "-jar", "app.jar"]
"""

    def _generate_generic(self, a: AnalysisResult) -> str:
        return """FROM ubuntu:24.04

WORKDIR /app
COPY . .

CMD ["bash"]
"""

    # --- Helpers ---

    def _python_install_cmd(self, a: AnalysisResult) -> str:
        return "pip install --no-cache-dir -r requirements.txt"

    def _node_commands(self, pm: str, a: AnalysisResult) -> tuple[str, str]:
        install_map = {
            "npm": "npm ci --ignore-scripts",
            "yarn": "yarn install --frozen-lockfile",
            "pnpm": "corepack enable && pnpm install --frozen-lockfile",
            "bun": "bun install --frozen-lockfile",
        }
        install = install_map.get(pm, "npm ci")
        build = a.build_command or "npm run build"
        return install, build

    def _node_copy_lockfile(self, pm: str) -> str:
        lockfiles = {
            "npm": "COPY package-lock.json* .",
            "yarn": "COPY yarn.lock .",
            "pnpm": "COPY pnpm-lock.yaml .",
            "bun": "COPY bun.lockb .",
        }
        return lockfiles.get(pm, "COPY package-lock.json* .")

    def _shell_to_cmd(self, cmd: str) -> list[str]:
        return cmd.split()

    def _to_cmd_array(self, cmd: str) -> str:
        parts = cmd.split()
        return "[" + ", ".join(f'"{p}"' for p in parts) + "]"
