"""Local W-01 commands; secrets stay in the server environment."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys

from dotenv import load_dotenv

from wayfinder.infrastructure.database import DatabaseHealth, upgrade_database
from wayfinder.settings import WebSettings


def main(argv=None) -> int:
    # PowerShell pipes can otherwise inherit CP1252 and crash on Vietnamese.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="web", description="WayFinder web development commands")
    parser.add_argument("--env-file", type=Path, help="Explicit server-only dotenv file")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    commands.add_parser("worker")
    commands.add_parser("check")
    commands.add_parser("media-smoke")
    create_admin = commands.add_parser("create-admin")
    create_admin.add_argument("--email", required=True)
    database = commands.add_parser("db").add_subparsers(dest="db_command", required=True)
    database.add_parser("upgrade")
    openapi = commands.add_parser("openapi").add_subparsers(dest="openapi_command", required=True)
    export = openapi.add_parser("export")
    export.add_argument("--output", type=Path, default=Path("src/web/openapi.json"))
    args = parser.parse_args(argv)
    if args.env_file:
        if not args.env_file.is_file():
            parser.error("Server dotenv file does not exist")
        load_dotenv(args.env_file, override=False)
    settings = WebSettings(_env_file=None)

    if args.command == "create-admin":
        if not settings.database_url:
            print("Thiếu WAYFINDER_DATABASE_URL.", file=sys.stderr)
            return 2
        from sqlalchemy.exc import SQLAlchemyError
        from wayfinder.application.accounts import AuthError
        from wayfinder.composition import compose_account_service

        health = None
        try:
            health = DatabaseHealth(settings.database_url)
            account_service = compose_account_service(settings, health.engine)
            password = getpass.getpass("Mật khẩu quản trị: ")
            account_service.create_admin(args.email, password)
        except AuthError as error:
            print(error.message, file=sys.stderr)
            return 1
        except (SQLAlchemyError, ValueError):
            print("Không thể tạo tài khoản quản trị; hãy kiểm tra cơ sở dữ liệu và cấu hình.", file=sys.stderr)
            return 1
        finally:
            if health is not None:
                health.close()
        print("Tài khoản quản trị đã được tạo.")
        return 0

    if args.command == "worker":
        print("Khung worker sẵn sàng. Vé W-14 bổ sung nhận và xử lý bản dựng.")
        return 0
    if args.command == "check":
        if not settings.test_database_url:
            print("PostgreSQL: thiếu WAYFINDER_TEST_DATABASE_URL; web check cần db-test.", file=sys.stderr)
            return 2
        health = DatabaseHealth(settings.test_database_url)
        try:
            if health() != "ok":
                print("PostgreSQL: db-test không truy cập được; hãy khởi động db-test.", file=sys.stderr)
                return 1
        finally:
            health.close()
        # Core tests supply their own model configuration and fake credentials.
        # Do not let the running server's transport override those test defaults.
        test_environment = {key: value for key, value in os.environ.items()
                            if not key.startswith("DOC2ROADMAP_")}
        test_environment["WAYFINDER_TEST_DATABASE_URL"] = settings.test_database_url
        return subprocess.call([sys.executable, "-m", "pytest", "--require-postgres"],
                               env=test_environment)
    if args.command == "db":
        if not settings.database_url:
            print("Thiếu WAYFINDER_DATABASE_URL.", file=sys.stderr)
            return 2
        upgrade_database(settings.database_url)
        print("Di trú cơ sở dữ liệu: tốt.")
        return 0
    if args.command == "openapi":
        from wayfinder.api import create_app, write_openapi
        from wayfinder.composition import WebServices

        write_openapi(create_app(settings, WebServices(health_check=lambda: "ok")), args.output)
        print(f"OpenAPI: {args.output}")
        return 0
    if args.command == "media-smoke":
        from wayfinder.infrastructure.media import media_smoke

        try:
            media_smoke()
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0

    import uvicorn
    from google.auth.exceptions import DefaultCredentialsError
    from wayfinder.api import create_app
    from wayfinder.composition import compose_services

    if not settings.database_url:
        print("Thiếu WAYFINDER_DATABASE_URL.", file=sys.stderr)
        return 2
    health = DatabaseHealth(settings.database_url)
    try:
        services = compose_services(settings, health_check=health, close=health.close)
    except (ValueError, DefaultCredentialsError):
        health.close()
        print("Cấu hình Vertex chưa hợp lệ: kiểm tra transport=vertex, project, location và ADC trên máy chủ.", file=sys.stderr)
        return 2
    try:
        uvicorn.run(create_app(settings, services), host=args.host, port=args.port)
    finally:
        health.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
