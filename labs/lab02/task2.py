import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import logging
import re
import sys

# Налаштування формату логування для консолі
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Регулярний вираз для розбору формату Apache/Nginx Access Log
LOG_LINE_REGEX = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<uri>\S+)\s+HTTP/[0-9.]+"\s+(?P<status>\d{3})\s+(?P<size>\d+|-)'
)

# Сигнатури атак
SQLI_REGEX = re.compile(r"('|--|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|OR\s+'1'='1)", re.IGNORECASE)
DIR_TRAVERSAL_REGEX = re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE)
XSS_REGEX = re.compile(r"(<script|%3Cscript|javascript:|alert\(|onerror=)", re.IGNORECASE)


def parse_log_time(time_str: str) -> datetime:
    """Перетворення строкового часу логу (наприклад, 27/Sep/2026:08:00:00 +0300) у datetime."""
    clean_time = time_str.split()[0]
    return datetime.strptime(clean_time, "%d/%b/%Y:%H:%M:%S")


def analyze_logs(log_file_path: str, top_n: int = 5, min_status: int = 400,
                 start_time: datetime | None = None, end_time: datetime | None = None):
    entries = []
    error_counter = Counter()
    ip_status_breakdown = defaultdict(Counter)
    attacks = []

    first_time = None
    last_time = None

    try:
        logging.info(f"Loading access log from {log_file_path}...")
        with open(log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                match = LOG_LINE_REGEX.match(line)
                if not match:
                    continue

                data = match.groupdict()
                ip = data["ip"]
                log_dt = parse_log_time(data["time"])
                method = data["method"]
                uri = data["uri"]
                status = int(data["status"])
                size = int(data["size"]) if data["size"] != "-" else 0

                # Фільтрація за часовим інтервалом
                if start_time and log_dt < start_time:
                    continue
                if end_time and log_dt > end_time:
                    continue

                if first_time is None or log_dt < first_time:
                    first_time = log_dt
                if last_time is None or log_dt > last_time:
                    last_time = log_dt

                entries.append({
                    "ip": ip,
                    "datetime": log_dt,
                    "method": method,
                    "uri": uri,
                    "status": status,
                    "size": size,
                    "raw_request": f"{method} {uri}"
                })

                # Підрахунок помилок (статус >= min_status, за дефолтом >= 400)
                if status >= min_status:
                    error_counter[ip] += 1
                    ip_status_breakdown[ip][status] += 1

                # Пошук сигнатур атак
                raw_req = f"{method} {uri}"
                if SQLI_REGEX.search(uri):
                    attacks.append({"type": "SQLi", "ip": ip, "request": raw_req})
                elif DIR_TRAVERSAL_REGEX.search(uri):
                    attacks.append({"type": "Directory Traversal", "ip": ip, "request": raw_req})
                elif XSS_REGEX.search(uri):
                    attacks.append({"type": "XSS", "ip": ip, "request": raw_req})

        # Повідомлення про оброблені записи
        if first_time and last_time:
            time_fmt = "%Y-%m-%d %H:%M:%S"
            logging.info(f"Processed {len(entries)} log entries from {first_time.strftime(time_fmt)} to {last_time.strftime(time_fmt)}.")
        else:
            logging.info(f"Processed {len(entries)} log entries.")

        # Виведення Топ-N IP з помилками
        print(f"\n=== Top-{top_n} IP Addresses with Error Statuses (4xx/5xx) ===")
        top_ips = error_counter.most_common(top_n)
        for ip, count in top_ips:
            statuses = ip_status_breakdown[ip]
            status_str = ", ".join([f"{st}: {cnt}" for st, cnt in sorted(statuses.items())])
            print(f"{ip:<15} - {count} errors ({status_str})")

        # Виведення виявлених атак
        print("\n=== Detected Attack Signatures ===")
        for att in attacks:
            logging.warning(f"Potential {att['type']} attack from {att['ip']}: \"{att['request']}\"")

        return {
            "total_entries": len(entries),
            "top_error_ips": [
                {"ip": ip, "total_errors": count, "statuses": dict(ip_status_breakdown[ip])}
                for ip, count in top_ips
            ],
            "detected_attacks": attacks
        }

    except FileNotFoundError:
        logging.error(f"File not found: {log_file_path}")
        sys.exit(1)


def save_report(report_data: dict, output_path: str, fmt: str):
    """Збереження звіту у JSON або CSV."""
    if fmt.lower() == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
    elif fmt.lower() == "csv":
        import csv
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric / Event", "IP", "Details / Request"])
            for item in report_data.get("top_error_ips", []):
                writer.writerow(["Top Error IP", item["ip"], f"Errors: {item['total_errors']}, Breakdown: {item['statuses']}"])
            for att in report_data.get("detected_attacks", []):
                writer.writerow([f"Attack ({att['type']})", att["ip"], att["request"]])

    logging.info(f"Analysis report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Web Server Access Log Analyzer")
    parser.add_argument("--log-file", required=True, help="Шлях до файлу access.log")
    parser.add_argument("--output", required=True, help="Шлях для збереження звіту")
    parser.add_argument("--min-status", type=int, default=400, help="Мінімальний статус-код помилки (default: 400)")
    parser.add_argument("--top", type=int, default=5, help="Кількість Топ-IP у звіті (default: 5)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Формат звіту (json/csv)")

    args = parser.parse_args()

    report = analyze_logs(
        log_file_path=args.log_file,
        top_n=args.top,
        min_status=args.min_status
    )

    if report:
        save_report(report, args.output, args.format)


if __name__ == "__main__":
    main()