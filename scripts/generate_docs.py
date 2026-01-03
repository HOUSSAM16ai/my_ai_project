#!/usr/bin/env python3
"""
Documentation Generation Script
Generates API documentation from OpenAPI and AsyncAPI specifications

Usage:
    python scripts/generate_docs.py
    python scripts/generate_docs.py --format html
    python scripts/generate_docs.py --output ./output
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class DocumentationGenerator:
    """Generate API documentation from contract specifications"""

    def __init__(self, output_dir: str = "docs/generated"):
        """
        Initialize documentation generator

        Args:
            output_dir: Directory to output generated documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.contracts_dir = Path("docs/contracts")
        self.openapi_dir = self.contracts_dir / "openapi"
        self.asyncapi_dir = self.contracts_dir / "asyncapi"
        self.grpc_dir = self.contracts_dir / "grpc"
        self.graphql_dir = self.contracts_dir / "graphql"

    def generate_all(self, format: str = "markdown") -> None:
        """
        Generate all documentation

        Args:
            format: Output format (markdown, html, pdf)
        """
        print("📚 Generating API Documentation...")
        print(f"   Format: {format}")
        print(f"   Output: {self.output_dir}")
        print()

        # Generate OpenAPI documentation
        self._generate_openapi_docs(format)

        # Generate AsyncAPI documentation
        self._generate_asyncapi_docs(format)

        # Generate gRPC documentation
        self._generate_grpc_docs(format)

        # Generate GraphQL documentation
        self._generate_graphql_docs(format)

        # Generate index page
        self._generate_index()

        print()
        print("✅ Documentation generation complete!")
        print(f"📂 Output directory: {self.output_dir.absolute()}")

    def _generate_openapi_docs(self, format: str) -> None:
        """Generate documentation from OpenAPI specifications"""
        print("🔵 Generating OpenAPI documentation...")

        if not self.openapi_dir.exists():
            print("   ⚠️  OpenAPI directory not found")
            return

        for spec_file in self.openapi_dir.glob("*.yaml"):
            print(f"   Processing: {spec_file.name}")

            try:
                # Load specification
                with open(spec_file) as f:
                    spec = yaml.safe_load(f)

                # Extract info
                info = spec.get("info", {})
                title = info.get("title", spec_file.stem)
                version = info.get("version", "1.0.0")

                # Generate markdown documentation
                md_content = self._generate_openapi_markdown(spec, title, version)

                # Save markdown
                output_file = self.output_dir / f"{spec_file.stem}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(md_content)

                print(f"   ✅ Generated: {output_file.name}")

                # Generate HTML if requested
                if format == "html":
                    self._generate_redoc_html(spec_file, title)

            except Exception as e:
                print(f"   ❌ Error: {e}")

    def _generate_openapi_markdown(
        self, spec: Dict, title: str, version: str
    ) -> str:
        """Generate Markdown documentation from OpenAPI spec"""
        lines = [
            f"# {title}",
            "",
            f"**Version**: {version}",
            "",
            "## Description",
            "",
            spec.get("info", {}).get("description", "No description available"),
            "",
            "## Base URL",
            "",
        ]

        # Servers
        servers = spec.get("servers", [])
        if servers:
            for server in servers:
                lines.append(f"- `{server['url']}` - {server.get('description', '')}")
        else:
            lines.append("- No servers defined")

        lines.extend(["", "## Endpoints", ""])

        # Paths
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            lines.append(f"### {path}")
            lines.append("")

            for method, operation in methods.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    lines.append(f"#### {method.upper()}")
                    lines.append("")
                    lines.append(
                        f"**Summary**: {operation.get('summary', 'No summary')}"
                    )
                    lines.append("")

                    if "description" in operation:
                        lines.append(f"**Description**: {operation['description']}")
                        lines.append("")

                    # Parameters
                    if "parameters" in operation:
                        lines.append("**Parameters**:")
                        lines.append("")
                        for param in operation["parameters"]:
                            required = " (required)" if param.get("required") else ""
                            lines.append(
                                f"- `{param['name']}` ({param['in']}){required}: "
                                f"{param.get('description', '')}"
                            )
                        lines.append("")

                    # Request body
                    if "requestBody" in operation:
                        lines.append("**Request Body**:")
                        lines.append("")
                        content = operation["requestBody"].get("content", {})
                        for media_type in content:
                            lines.append(f"Content-Type: `{media_type}`")
                        lines.append("")

                    # Responses
                    lines.append("**Responses**:")
                    lines.append("")
                    for status, response in operation.get("responses", {}).items():
                        lines.append(
                            f"- `{status}`: {response.get('description', '')}"
                        )
                    lines.append("")

        return "\n".join(lines)

    def _generate_redoc_html(self, spec_file: Path, title: str) -> None:
        """Generate Redoc HTML for OpenAPI spec"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title} - API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url="../contracts/openapi/{spec_file.name}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""
        output_file = self.output_dir / f"{spec_file.stem}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"   ✅ Generated HTML: {output_file.name}")

    def _generate_asyncapi_docs(self, format: str) -> None:
        """Generate documentation from AsyncAPI specifications"""
        print("🟣 Generating AsyncAPI documentation...")

        if not self.asyncapi_dir.exists():
            print("   ⚠️  AsyncAPI directory not found")
            return

        for spec_file in self.asyncapi_dir.glob("*.yaml"):
            print(f"   Processing: {spec_file.name}")

            try:
                with open(spec_file) as f:
                    spec = yaml.safe_load(f)

                info = spec.get("info", {})
                title = info.get("title", spec_file.stem)

                md_content = self._generate_asyncapi_markdown(spec, title)

                output_file = self.output_dir / f"{spec_file.stem}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(md_content)

                print(f"   ✅ Generated: {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

    def _generate_asyncapi_markdown(self, spec: Dict, title: str) -> str:
        """Generate Markdown documentation from AsyncAPI spec"""
        lines = [
            f"# {title} (AsyncAPI)",
            "",
            "## Description",
            "",
            spec.get("info", {}).get("description", "No description available"),
            "",
            "## Channels",
            "",
        ]

        channels = spec.get("channels", {})
        for channel, config in channels.items():
            lines.append(f"### {channel}")
            lines.append("")

            if "subscribe" in config:
                lines.append("**Subscribe**")
                lines.append(
                    f"- Summary: {config['subscribe'].get('summary', '')}"
                )
                lines.append("")

            if "publish" in config:
                lines.append("**Publish**")
                lines.append(f"- Summary: {config['publish'].get('summary', '')}")
                lines.append("")

        return "\n".join(lines)

    def _generate_grpc_docs(self, format: str) -> None:
        """Generate documentation from gRPC proto files"""
        print("🟢 Generating gRPC documentation...")

        if not self.grpc_dir.exists():
            print("   ⚠️  gRPC directory not found")
            return

        for proto_file in self.grpc_dir.glob("*.proto"):
            print(f"   Processing: {proto_file.name}")

            try:
                md_content = self._generate_grpc_markdown(proto_file)

                output_file = self.output_dir / f"{proto_file.stem}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(md_content)

                print(f"   ✅ Generated: {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

    def _generate_grpc_markdown(self, proto_file: Path) -> str:
        """Generate Markdown documentation from proto file"""
        lines = [
            f"# {proto_file.stem} (gRPC)",
            "",
            "## Proto Definition",
            "",
            "```protobuf",
        ]

        with open(proto_file) as f:
            lines.append(f.read())

        lines.extend(["```", ""])

        return "\n".join(lines)

    def _generate_graphql_docs(self, format: str) -> None:
        """Generate documentation from GraphQL schema"""
        print("🟡 Generating GraphQL documentation...")

        if not self.graphql_dir.exists():
            print("   ⚠️  GraphQL directory not found")
            return

        for schema_file in self.graphql_dir.glob("*.graphql"):
            print(f"   Processing: {schema_file.name}")

            try:
                md_content = self._generate_graphql_markdown(schema_file)

                output_file = self.output_dir / f"{schema_file.stem}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(md_content)

                print(f"   ✅ Generated: {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

    def _generate_graphql_markdown(self, schema_file: Path) -> str:
        """Generate Markdown documentation from GraphQL schema"""
        lines = [
            f"# {schema_file.stem} (GraphQL)",
            "",
            "## Schema Definition",
            "",
            "```graphql",
        ]

        with open(schema_file) as f:
            lines.append(f.read())

        lines.extend(["```", ""])

        return "\n".join(lines)

    def _generate_index(self) -> None:
        """Generate index page for all documentation"""
        print("📋 Generating index page...")

        lines = [
            "# API Documentation Index",
            "",
            "## Available Documentation",
            "",
        ]

        # List all generated markdown files
        for md_file in sorted(self.output_dir.glob("*.md")):
            if md_file.name != "index.md":
                lines.append(f"- [{md_file.stem}]({md_file.name})")

        lines.extend(
            [
                "",
                "## Interactive Documentation",
                "",
                "HTML documentation with Redoc:",
                "",
            ]
        )

        # List all generated HTML files
        for html_file in sorted(self.output_dir.glob("*.html")):
            lines.append(f"- [{html_file.stem}]({html_file.name})")

        lines.extend(
            [
                "",
                "---",
                "",
                "**Generated**: Automatically by documentation generator",
                "**Source**: Contract specifications in `docs/contracts/`",
            ]
        )

        index_file = self.output_dir / "index.md"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"   ✅ Generated: {index_file.name}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate API documentation from contract specifications"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "html", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output",
        default="docs/generated",
        help="Output directory (default: docs/generated)",
    )

    args = parser.parse_args()

    generator = DocumentationGenerator(output_dir=args.output)

    try:
        if args.format in ["markdown", "both"]:
            generator.generate_all("markdown")

        if args.format in ["html", "both"]:
            generator.generate_all("html")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
